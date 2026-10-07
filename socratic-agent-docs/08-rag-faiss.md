# RAG Architecture (FAISS)

*Socratic Agent project document. [Index](README.md) | [← Previous](07-socratic-agent.md) | [Next →](09-api.md)*

---

## 17. RAG Architecture

### 17.1 Pipeline

```text
Educational Document
       ↓
Document Processing
       ↓
Text Chunking
       ↓
Embedding Generation
       ↓
FAISS Index
       ↓
Similarity Search
       ↓
Relevant Context
       ↓
Socratic Agent
       ↓
LLM
```

### 17.2 Ingestion (Offline Path)

| Step | Action | Detail |
|---|---|---|
| 1 | Upload | Administrator uploads PDF, TXT or MD (maximum 10 MB). The API checks extension, MIME type and file signature. |
| 2 | Deduplicate | The service computes SHA-256. A duplicate in the same subject gives `409`. |
| 3 | Register | The service inserts `knowledge_documents` with status `pending`. The API returns `202`. |
| 4 | Process | A background task sets `processing`. It extracts text (`PyPDFLoader` for PDF, `TextLoader` for TXT and MD). |
| 5 | Chunk | `RecursiveCharacterTextSplitter` with `chunk_size = 800` and `chunk_overlap = 120` characters. |
| 6 | Persist chunks | The service inserts `document_chunks` rows. PostgreSQL assigns `vector_id` to each row. |
| 7 | Embed | The embedding model (`sentence-transformers/all-MiniLM-L6-v2`, 384 dimensions) creates vectors. The code normalizes them (L2) so that inner product equals cosine similarity. |
| 8 | Index | The vector store adds the vectors to the **index of the subject** with `ids = vector_id`. It saves the index file (write to a temporary file, then rename). |
| 9 | Link | The service saves `embedding_reference = str(vector_id)` and sets the document status to `indexed`. |
| 10 | On failure | The service removes the added `vector_id` values from the index, keeps the document row, sets `failed` and saves `error_message`. |

### 17.3 Retrieval (Online Path)

| Step | Action |
|---|---|
| 1 | The agent builds the query: core question + latest student message (maximum 500 characters). |
| 2 | The retriever embeds the query with the same embedding model and normalizes it. |
| 3 | FAISS searches the index of the session's subject and returns the top `RAG_TOP_K` (default 4) `vector_id` values with scores. |
| 4 | The retriever removes results with a score below `RAG_MIN_SCORE` (default 0.35). |
| 5 | The retriever reads the chunk text, `document_id` and document title from PostgreSQL for the remaining `vector_id` values (one query, short read-only session). It ignores a `vector_id` that has no row. |
| 6 | The retriever returns `RetrievedChunk` objects. The agent places them in the prompt. |
| 7 | The service saves the chunk IDs in `messages.retrieved_chunk_ids`. |

The retriever is a component that the service injects into the agent. It opens its own short database session. The agent itself still has no database access (rule R-02), and no connection stays open during an LLM call (rule R-04).

### 17.4 How PostgreSQL and FAISS Work Together

```text
              PostgreSQL                                   FAISS (one file for each subject)
   ┌─────────────────────────────────┐          ┌────────────────────────────────────────┐
   │ knowledge_documents             │          │ <FAISS_INDEX_DIR>/<subject_id>.faiss   │
   │  id, subject_id, title,         │          │  IndexIDMap2(IndexFlatIP, 384 dims)    │
   │  status, content_hash           │          │   id     = vector_id (int64)           │
   │ document_chunks                 │ ◄──────► │   vector = normalized embedding        │
   │  id, vector_id, document_id,    │  vector_id│  (no text, no metadata)               │
   │  content, chunk_index           │          └────────────────────────────────────────┘
   └─────────────────────────────────┘
   messages.retrieved_chunk_ids  ◄── agent records which chunk IDs it used
```

- The link is the integer `vector_id`. PostgreSQL creates it. FAISS uses it as the vector ID.
- PostgreSQL is the source of truth. `scripts/reindex.py` rebuilds all index files from `document_chunks` (it re-embeds the text).
- Save the embedding model name and dimension in `<FAISS_INDEX_DIR>/manifest.json`. At startup, the app compares the manifest with `EMBEDDING_MODEL`. If they differ, the app must re-index all chunks.

### 17.5 FAISS Design

| Aspect | Decision |
|---|---|
| Index type | `IndexFlatIP` (exact search) inside `IndexIDMap2`. It supports custom int64 IDs and `remove_ids`. |
| Similarity | Cosine similarity. The code normalizes vectors and queries, then uses inner product. |
| Subject filter | FAISS has no metadata filter. The system keeps **one index for each subject**. |
| Persistence | One file for each subject: `<FAISS_INDEX_DIR>/<subject_id>.faiss`. The app writes to a temporary file and renames it, so a crash cannot corrupt the index. |
| Loading | The app loads all index files into memory at startup. A missing file gives an empty index. |
| Concurrency | A `threading.RLock` protects add, remove and save. Search and write do not run at the same time. |
| Size | Exact search is enough for about 100,000 chunks. Use an IVF or HNSW index for larger collections (change only `FaissVectorStore`). |

```python
# app/rag/vector_store.py
from typing import Protocol

class VectorStore(Protocol):
    def add(self, subject_id: str, vector_ids: list[int], texts: list[str]) -> None: ...
    def remove(self, subject_id: str, vector_ids: list[int]) -> None: ...
    def search(self, subject_id: str, query: str, k: int) -> list[tuple[int, float]]: ...  # (vector_id, score)
    def rebuild(self, subject_id: str, vector_ids: list[int], texts: list[str]) -> None: ...
    def health(self) -> bool: ...
```

```python
# app/rag/vector_store_faiss.py
import os
import threading
from pathlib import Path

import faiss
import numpy as np


class FaissVectorStore:
    def __init__(self, index_dir: str, embeddings, dim: int = 384):
        self.dir, self.emb, self.dim = Path(index_dir), embeddings, dim
        self.dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._indexes: dict[str, faiss.Index] = {}
        for f in self.dir.glob("*.faiss"):
            self._indexes[f.stem] = faiss.read_index(str(f))

    def _new_index(self) -> faiss.Index:
        return faiss.IndexIDMap2(faiss.IndexFlatIP(self.dim))

    def _vectors(self, texts: list[str]) -> np.ndarray:
        v = np.asarray(self.emb.embed_documents(texts), dtype="float32")
        faiss.normalize_L2(v)
        return v

    def _save(self, subject_id: str) -> None:
        path = self.dir / f"{subject_id}.faiss"
        tmp = path.with_suffix(".tmp")
        faiss.write_index(self._indexes[subject_id], str(tmp))
        os.replace(tmp, path)                       # atomic rename

    def add(self, subject_id, vector_ids, texts):
        vecs = self._vectors(texts)                 # embed outside the lock (slow)
        with self._lock:
            idx = self._indexes.setdefault(subject_id, self._new_index())
            idx.add_with_ids(vecs, np.asarray(vector_ids, dtype="int64"))
            self._save(subject_id)

    def remove(self, subject_id, vector_ids):
        with self._lock:
            idx = self._indexes.get(subject_id)
            if idx is not None:
                idx.remove_ids(np.asarray(vector_ids, dtype="int64"))
                self._save(subject_id)

    def search(self, subject_id, query, k):
        q = np.asarray([self.emb.embed_query(query)], dtype="float32")
        faiss.normalize_L2(q)
        with self._lock:
            idx = self._indexes.get(subject_id)
            if idx is None or idx.ntotal == 0:
                return []
            scores, ids = idx.search(q, k)
        return [(int(i), float(s)) for i, s in zip(ids[0], scores[0]) if i != -1]

    def rebuild(self, subject_id, vector_ids, texts):
        vecs = self._vectors(texts)
        idx = self._new_index()
        idx.add_with_ids(vecs, np.asarray(vector_ids, dtype="int64"))
        with self._lock:
            self._indexes[subject_id] = idx
            self._save(subject_id)

    def health(self) -> bool:
        return self.dir.exists() and os.access(self.dir, os.W_OK)
```

The embedding object is `HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)` from `langchain-huggingface`. Build it once at startup.

### 17.6 Consistency Rules

| Case | Rule |
|---|---|
| Ingestion fails after some vectors exist | Remove the `vector_id` values of the document from the index. Set the document to `failed`. |
| Delete document | 1. Read the `vector_id` values from `document_chunks`. 2. Remove them from the index. 3. Delete the PostgreSQL row (chunks cascade). If step 2 fails, stop and return an error. |
| Re-index document | Set `processing`. Remove old vectors. Delete chunk rows. Run steps 4 to 9 of Section 17.2. |
| Vector without a chunk row (orphan) | Harmless. The retriever ignores it. `reindex.py` removes it. |
| Chunk row without a vector | The chunk is not searchable. `reindex.py` adds it. |
| Index file lost or corrupt | Run `scripts/reindex.py --all`. It rebuilds every index file from PostgreSQL. |
| Delete subject | Blocked while documents exist (`RESTRICT`). |

### 17.7 Behavior Without Retrieval

| Situation | `rag_status` | Agent behavior |
|---|---|---|
| `RAG_ENABLED=false` | `off` | `NullRetriever` returns no chunks. The prompt says that no reference material exists. |
| No chunk above the score threshold | `empty` | General knowledge mode. The agent asks conceptual questions and does not state specific facts that it cannot verify. |
| Index or database error during retrieval | `error` | The system logs the error and continues in general knowledge mode. |

### 17.8 Retrieval Service

```python
# app/rag/retriever.py
from sqlalchemy import select

class KnowledgeRetriever:
    def __init__(self, store: VectorStore, session_factory, k: int, min_score: float):
        self.store, self.session_factory, self.k, self.min_score = store, session_factory, k, min_score

    def retrieve(self, subject_id: str, query: str):
        try:
            hits = [(i, s) for i, s in self.store.search(subject_id, query, self.k) if s >= self.min_score]
            if not hits:
                return [], "empty"
            with self.session_factory() as db:                      # short read-only session
                rows = db.execute(
                    select(DocumentChunk.vector_id, DocumentChunk.id, DocumentChunk.document_id,
                           DocumentChunk.content, KnowledgeDocument.title)
                    .join(KnowledgeDocument, KnowledgeDocument.id == DocumentChunk.document_id)
                    .where(DocumentChunk.vector_id.in_([i for i, _ in hits]))
                ).all()
            by_vid = {r.vector_id: r for r in rows}
            chunks = [RetrievedChunk(chunk_id=str(r.id), document_id=str(r.document_id),
                                     title=r.title, content=r.content, score=score)
                      for vid, score in hits if (r := by_vid.get(vid))]
            return chunks, ("ok" if chunks else "empty")
        except Exception:
            logger.exception("retrieval failed")
            return [], "error"


class NullRetriever:
    def retrieve(self, subject_id: str, query: str):
        return [], "off"
```

---

*[Index](README.md) | [← Previous](07-socratic-agent.md) | [Next →](09-api.md)*
