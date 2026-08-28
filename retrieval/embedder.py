import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import numpy as np

logger = logging.getLogger(__name__)


class Embedder:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self._load_model()

    def _load_model(self):
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")

    def embed(self, text: str) -> Optional[np.ndarray]:
        if not self.model:
            return None

        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            return None

    def embed_batch(self, texts: List[str]) -> Optional[List[np.ndarray]]:
        if not self.model:
            return None

        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return list(embeddings)
        except Exception as e:
            logger.error(f"Batch embedding failed: {e}")
            return None

    def similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        if embedding1 is None or embedding2 is None:
            return 0.0

        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))
