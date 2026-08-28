import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from .documents import Document, DocumentLoader
from .embedder import Embedder
from llm.schemas import EvidenceChunk

logger = logging.getLogger(__name__)


class Retriever:
    def __init__(self, embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.embedder = Embedder(embedding_model)
        self.documents: List[Document] = []
        self.document_embeddings: Dict[str, Any] = {}
        self._load_and_index_corpus()

    def _load_and_index_corpus(self):
        documents = DocumentLoader.load_corpus()
        self.documents = documents

        for doc in documents:
            if self.embedder.model:
                embedding = self.embedder.embed(doc.content)
                self.document_embeddings[doc.doc_id] = {
                    "embedding": embedding,
                    "document": doc,
                }

        logger.info(f"Indexed {len(self.documents)} documents for retrieval")

    def retrieve(self, query: str, top_k: int = 3) -> List[EvidenceChunk]:
        if not self.embedder.model or not query:
            return []

        query_embedding = self.embedder.embed(query)
        if query_embedding is None:
            return []

        scores = []

        for doc_id, doc_data in self.document_embeddings.items():
            doc_embedding = doc_data["embedding"]
            document = doc_data["document"]

            if doc_embedding is None:
                continue

            similarity = self.embedder.similarity(query_embedding, doc_embedding)

            scores.append(
                {
                    "doc_id": doc_id,
                    "document": document,
                    "similarity": similarity,
                }
            )

        scores.sort(key=lambda x: x["similarity"], reverse=True)

        results = []
        for item in scores[:top_k]:
            doc = item["document"]

            results.append(
                EvidenceChunk(
                    document_id=doc.doc_id,
                    title=doc.title,
                    version=doc.version,
                    effective_date=doc.effective_date,
                    content=doc.content,
                    similarity=item["similarity"],
                )
            )

        return results
