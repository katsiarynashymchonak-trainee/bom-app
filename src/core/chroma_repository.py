# src/core/chroma_repository.py

from typing import List, Dict, Any, Optional
import chromadb


# Репозиторий для работы с ChromaDB
class ChromaRepository:
    _instance: Optional["ChromaRepository"] = None

    # Инициализация клиента и коллекции
    def __init__(self):
        self.client = chromadb.PersistentClient(path="./data/chroma")

        self.collection = self.client.get_or_create_collection(
            name="bom_components",
            metadata={"hnsw:space": "cosine"},
        )

    # Синглтон доступ к экземпляру
    @classmethod
    def instance(cls) -> "ChromaRepository":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # Добавление или обновление векторных записей
    def upsert(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    # Векторный запрос к коллекции
    def query(
        self,
        query_embedding: List[float],
        n_results: int = 20,
        where: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
        )
        return {
            "ids": result.ids,
            "distances": result.distances,
            "metadatas": result.metadatas,
            "embeddings": result.embeddings,
        }

    # Удаление записей по идентификаторам
    def delete(self, ids: List[str]) -> None:
        self.collection.delete(ids=ids)
