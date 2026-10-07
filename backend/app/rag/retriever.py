"""RAG retriever (docs Sec 17). NullRetriever is complete; FAISS retriever is Phase 7."""


class NullRetriever:
    """Used when RAG_ENABLED=false. Always returns ([], "off")."""

    def retrieve(self, subject_id: str, query: str):
        return [], "off"


class KnowledgeRetriever:
    """Phase 7: FAISS + PostgreSQL two-step retrieval."""

    def __init__(self, *args, **kwargs):
        raise NotImplementedError("TODO(phase-7): build KnowledgeRetriever over FaissVectorStore")

    def retrieve(self, subject_id: str, query: str, top_k: int = 4):
        raise NotImplementedError("TODO(phase-7): FAISS search then chunk-text lookup")
