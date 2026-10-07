"""RAG retriever wrapper -- Phase 7 (docs Sec 17)."""


class KnowledgeRetriever:
    def __init__(self, retriever=None):
        self.retriever = retriever

    def retrieve(self, subject_id: str, query: str):
        raise NotImplementedError("TODO(phase-7): FAISS top-K retrieval for subject")
