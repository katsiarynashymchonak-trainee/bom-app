import threading
from typing import List

from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """
    Синглтон‑обёртка над SentenceTransformer для генерации эмбеддингов.
    Используется во всём приложении как единый источник эмбеддингов.
    """

    _instance = None
    _lock = threading.Lock()

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    @classmethod
    def instance(cls) -> "EmbeddingService":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def encode(self, text: str) -> List[float]:
        """
        Кодирует одну строку текста в вектор.
        """
        if not text:
            text = ""
        emb = self.model.encode(text)
        return emb.tolist()

    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Кодирует список строк в список векторов.
        """
        texts = [t if t is not None else "" for t in texts]
        embs = self.model.encode(texts, batch_size=64, show_progress_bar=False)
        return [e.tolist() for e in embs]
