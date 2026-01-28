from typing import List, Dict, Any, Optional
import chromadb


# Репозиторий для работы с ChromaDB
class ChromaRepository:
    _instance: Optional["ChromaRepository"] = None

    def __init__(self):
        # дисковое хранилище без RAM кэшей
        self.client = chromadb.PersistentClient(path="./data/chroma")

        # коллекция с HNSW и косинусной метрикой
        self.collection = self.client.get_or_create_collection(
            name="bom_components",
            metadata={"hnsw:space": "cosine"},
        )

    # синглтон доступ к экземпляру
    @classmethod
    def instance(cls) -> "ChromaRepository":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # базовые операции
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

    def delete(self, ids: List[str]) -> None:
        self.collection.delete(ids=ids)

    def query(
        self,
        query_embedding: List[float],
        n_results: int = 20,
        where: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        # быстрый HNSW поиск по вектору
        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
        )

        return {
            "ids": result.get("ids", []),
            "distances": result.get("distances", []),
            "metadatas": result.get("metadatas", []),
            "embeddings": result.get("embeddings", []),
        }

    # массовые операции для полного пересоздания
    def upsert_batch(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        if not ids:
            return

        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    def delete_batch(self, ids: List[str]) -> None:
        if not ids:
            return
        self.collection.delete(ids=ids)

    # утилиты для чтения ID и метаданных
    def get_all_ids(self) -> List[str]:
        # чтение ID батчами для избежания RAM пиков
        out: List[str] = []
        batch_size = 500
        offset = 0

        while True:
            try:
                result = self.collection.get(
                    include=[],
                    limit=batch_size,
                    offset=offset
                )
            except Exception:
                break

            ids = result.get("ids", [])
            if not ids:
                break

            out.extend(ids)
            offset += batch_size

        return out

    def get_metadatas(self, ids: List[str]) -> Dict[str, Dict[str, Any]]:
        # чтение метаданных батчами для избежания ошибки SQLite
        if not ids:
            return {}

        out: Dict[str, Dict[str, Any]] = {}
        batch_size = 500

        for i in range(0, len(ids), batch_size):
            batch = ids[i:i + batch_size]

            try:
                result = self.collection.get(
                    ids=batch,
                    include=["metadatas"]
                )
            except Exception:
                continue

            if not result:
                continue

            for uid, meta in zip(result["ids"], result["metadatas"]):
                out[uid] = meta or {}

        return out

    # полное пересоздание коллекции
    def reset_collection(self) -> None:
        self.client.delete_collection("bom_components")
        self.collection = self.client.get_or_create_collection(
            name="bom_components",
            metadata={"hnsw:space": "cosine"},
        )
