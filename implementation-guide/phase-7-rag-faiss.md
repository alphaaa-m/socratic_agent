# Phase 7: RAG with FAISS (Student)

*[Index](README.md) | [← Phase 6](phase-6-summary-and-progress.md) | [Next: Phase 8 →](phase-8-testing-and-evaluation.md)*

**Owner:** Student. **Time:** about 2 weeks. **Branch:** `phase-7/<your-name>`.

> **Parallel work:** this phase needs only Phase 3 and Phase 4. Two students can build it while another student builds Phases 5 and 6. Merge in this order: 5, 6, 7.

## 7.1 Goal

An administrator uploads course documents. The system splits them into chunks, creates embeddings, and stores the vectors in a **FAISS** index (one index for each subject). The agent retrieves relevant chunks and uses them in the prompt. PostgreSQL keeps the chunk text. The feature is controlled by `RAG_ENABLED`.

## 7.2 Read First

| Topic | Design section |
|---|---|
| RAG design | §17 (all). Read it twice. |
| Tables | §5.4.8 `knowledge_documents`, §5.4.9 `document_chunks` (note `vector_id`) |
| Data flow | §8.3 PostgreSQL and FAISS: who stores what |
| API | §18.10 Document APIs, §18.13 (upload, retrieval test) |
| Sequence | §22.5 RAG ingestion and retrieval |
| Requirements | §9.11 RAG, §9.16 Document management |
| Errors | §27.2 (RAG failure, empty result, document processing failure) |
| Tests | §24.7 RAG tests |

## 7.3 Your Work List

```bash
grep -rn "TODO(phase-7)" backend frontend
```

### Backend: RAG package

| # | Task | File | Notes |
|---|---|---|---|
| 1 | Embeddings | `app/rag/embeddings.py` | `get_embeddings(settings)` returns `HuggingFaceEmbeddings(model_name=settings.embedding_model)`. Build once and reuse. |
| 2 | Loaders | `app/rag/loaders.py` | `load_text(path, ext)`: PDF with `PyPDFLoader`, TXT and MD with `TextLoader`. Return clean text. An empty result is an error. |
| 3 | Chunking | `app/rag/chunking.py` | `split(text, size, overlap)` with `RecursiveCharacterTextSplitter` (800 / 120). Remove empty chunks. |
| 4 | FAISS store | `app/rag/vector_store_faiss.py` | `FaissVectorStore` (§17.5): `add`, `remove`, `search`, `rebuild`, `health`. One `IndexIDMap2(IndexFlatIP)` for each subject. Normalize vectors. Save with a temporary file and `os.replace`. Use a lock. Load all files at startup. |
| 5 | Manifest check | same | Save and check `manifest.json` (embedding model name and dimension) in the index folder. If different from the settings, log an error and report `health() == False`. |
| 6 | Retriever | `app/rag/retriever.py` | `KnowledgeRetriever.retrieve(subject_id, query)` (§17.8). Search, apply `RAG_MIN_SCORE`, read the chunk text and title from PostgreSQL in one query with a **short own session**, ignore vectors without a row. Return `(chunks, rag_status)`. Never raise: return `([], "error")`. |
| 7 | Factory | `app/agents/factory.py` | If `RAG_ENABLED`, build the real store and retriever. If not, use `NullRetriever`. |
| 8 | Agent wrapper | `capabilities/knowledge_retriever.py` | Thin wrapper that calls the retriever. |
| 9 | Use chunks in the prompt | `prompt_builder.py` (check) | Chunks go inside `<reference_material>`. The evaluator also gets them. (Phase 4 and 5 already accept chunks. Check that it works.) |
| 10 | Save used chunks | `TutoringService` write phase | Save `retrieved_chunk_ids` in the agent message. |

### Backend: documents

| # | Task | File | Notes |
|---|---|---|---|
| 11 | Upload | `DocumentService.upload` | Check extension, MIME type, file signature (magic bytes) and size (`MAX_UPLOAD_MB`). Compute SHA-256. Duplicate in the same subject gives `409`. Insert `knowledge_documents` with status `pending`. Start the background task. Return `202`. |
| 12 | Ingestion task | `app/rag/ingestion.py` | Steps 4-10 of §17.2: set `processing` → extract → chunk → insert `document_chunks` (PostgreSQL gives `vector_id`) → embed and add to the subject index → set `embedding_reference = str(vector_id)` → set `indexed`. On any error: remove the added vectors, set `failed`, save `error_message`. Use its **own** database session (a background task has no request session). |
| 13 | List, get, chunks | `DocumentService` | Filters and pagination. Admin only. |
| 14 | Delete | `DocumentService.delete` | Rules of §17.6: read `vector_id` values → remove from the index → delete the row. If the index removal fails, stop and return `502`. |
| 15 | Re-index | `DocumentService.reindex` | Set `processing`, remove vectors, delete chunk rows, run the ingestion again. Return `202`. |
| 16 | Retrieval test | `DocumentService.search`, `POST /documents/search` | Admin only. Return chunks with scores. |
| 17 | Router | `app/api/v1/documents.py` | Define `/documents/search` **before** `/documents/{document_id}` so that the path is not read as an ID. |
| 18 | Health | `app/api/v1/health.py` | Report `vector_store` as `ok`, `error` or `disabled`. |
| 19 | Reindex script | `scripts/reindex.py` | `--all` or `--subject <id>`: rebuild each index from `document_chunks` (re-embed the stored text) with `rebuild`. Remove orphan vectors. |

### Frontend

| # | Task | File | Notes |
|---|---|---|---|
| 20 | Services and hooks | `services/documents.ts`, `hooks/useDocuments.ts` | Poll the list every 3 seconds while a document is `pending` or `processing`. |
| 21 | Documents page | `app/(app)/admin/documents/page.tsx`, `components/admin/DocumentUploadForm.tsx`, `DocumentTable.tsx` | Upload form (file, subject, title, description, source). Table with a status badge, re-index and delete (with confirmation). Show `error_message` for failed documents. |
| 22 | Retrieval tester | `components/admin/RetrievalTester.tsx` | `Dialog`: subject, query, top k. Show chunks with scores. |

## 7.4 Hints

- **FAISS stores only vectors.** If you try to store text in it, stop and read §17.4.
- The `vector_id` is created by PostgreSQL **when you insert the chunk row**. So: insert the rows first, `flush()`, read the IDs, then embed and add to FAISS.
- Use inner product on **normalized** vectors. Without normalization the scores are not cosine similarity and the `0.35` threshold means nothing.
- `faiss.read_index` on an `IndexIDMap2` file returns an `IndexIDMap2`. `remove_ids` works on it.
- Embedding is slow. Do it **outside** the lock and outside any database transaction that you do not need.
- A FastAPI `BackgroundTasks` function runs after the response. Create a new `SessionLocal()` inside it.
- Test with a **fake embedding class** (returns deterministic small vectors from a hash of the text). Then no model download is needed in CI.
- The first real run downloads the embedding model. Do it once before the demo.
- Make the retriever's database session factory a constructor argument (`session_factory`). Then tests can pass the test session.
- Keep a gold set `tests/rag/gold.json`: 20 queries, each with the text of the expected chunk. You need it in Phase 8.

## 7.5 Tests

| Test | Checks |
|---|---|
| Chunking (unit) | Size and overlap limits. No empty chunks. Stable order. |
| Loaders (unit) | PDF, TXT, MD sample files. Empty file raises an error. |
| FaissVectorStore (unit, fake embeddings) | Add and search. `remove` deletes. Save and load round trip. Unknown subject gives `[]`. Atomic save (temporary file is not left behind). Scores are cosine values. |
| Subject separation | A query in subject A never returns vectors of subject B. |
| Ingestion (integration) | Status `pending` → `processing` → `indexed`. Chunk rows have `vector_id` and `embedding_reference`. The vectors are in the index. |
| Ingestion failure | Force an error after some vectors were added: the vectors are removed and the status is `failed` with `error_message`. |
| Duplicate upload | `409`. |
| File checks | `415` for a wrong type (also a `.txt` file that is really a binary). `413` for a large file. |
| Delete | Vectors removed, rows gone. If the removal fails: `502` and the row still exists. |
| Re-index | Idempotent: the same chunk count and no duplicate vectors. |
| Retriever | Returns chunks above the threshold. Skips orphan vectors. Empty result gives `rag_status="empty"`. Index error gives `"error"` without raising. |
| Agent turn with RAG | Chunks appear in the prompt (inspect the `FakeGateway` calls). `retrieved_chunk_ids` is saved. |
| `RAG_ENABLED=false` | Tutoring works. `NullRetriever` is used. |
| Documents API | `403` for students. Pagination. `/documents/search` works. |
| Retrieval quality | Gold set: hit rate at k=4 ≥ 0.85 (with the real embedding model, marked `slow`). |
| Frontend | Upload form validation. Status polling stops when indexed. |

## 7.6 Definition of Done

- [ ] All `TODO(phase-7)` markers are removed.
- [ ] Phase 7 tests and the full suite pass. Lint and type checks pass.
- [ ] An administrator uploads a PDF. The status changes to `indexed`. `psql` shows chunk rows with `vector_id`. The folder `FAISS_INDEX_DIR` has a `<subject_id>.faiss` file.
- [ ] The retrieval tester returns the expected chunks for 3 test queries.
- [ ] A tutoring session in that subject uses the material: `messages.retrieved_chunk_ids` is not empty, and the agent's questions refer to the material.
- [ ] Deleting the document removes its vectors (the retrieval tester no longer finds it).
- [ ] After you delete the index folder and run `python scripts/reindex.py --all`, retrieval works again.
- [ ] With `RAG_ENABLED=false`, everything from Phases 1 to 6 still works.

## 7.7 Demo for the Instructor

1. Upload a short PDF as admin. Show the status changes, the `document_chunks` rows and the index file.
2. Use the retrieval tester with a good query and an unrelated query (empty result).
3. Run a tutoring session. Show the retrieved chunk IDs in the database.
4. Stop the app, delete the index folder, run `reindex.py`, and search again.
5. Set `RAG_ENABLED=false` and show that tutoring still works.

## 7.8 Common Mistakes

| Mistake | Why it is a problem |
|---|---|
| Storing chunk text only in FAISS or in a pickle file | PostgreSQL is the source of truth. A lost index file must be rebuildable. |
| Forgetting to normalize vectors | Inner product is not cosine similarity. The score threshold fails. |
| One index for all subjects with a manual filter | FAISS cannot filter. Use one index for each subject. |
| Using the request database session in the background task | The session is closed after the response. |
| Running two backend workers | Two processes can write the same index file. Use one worker (§28.6). |
| Saving the index directly to the final file name | A crash can corrupt it. Write a temporary file, then rename. |
| Letting a retrieval error stop the tutoring turn | Retrieval failure must not break a turn (NFR-AVL-03). Return `rag_status="error"`. |
| Deleting the row before removing the vectors | Then the vectors are orphans, or you lose the IDs. Remove vectors first. |
