from typing import Dict, List, Any

from sqlalchemy import select

from src.core.chroma_repository import ChromaRepository
from src.db.database import SessionLocal
from src.db.models import ComponentDB
from src.ml.embedding_service import EmbeddingService


class CrossMatchingService:

    def __init__(self):
        self.chroma = ChromaRepository.instance()
        self.embedder = EmbeddingService.instance()

    def _get_session(self):
        return SessionLocal()

    def _get_component(self, component_id: int):
        with self._get_session() as session:
            return session.get(ComponentDB, component_id)

    def find_similar(
            self,
            component_id: int,
            top_k: int = 10,
            same_level_only: bool = False,
    ) -> Dict[str, List[Dict[str, Any]]]:

        obj = self._get_component(component_id)
        if not obj or not obj.embedding_vector:
            return {
                "same_assembly": [],
                "other_assemblies": [],
                "analogs": []
            }

        query_emb = obj.embedding_vector

        # Получаем большой пул кандидатов
        result = self.chroma.query(
            query_embedding=query_emb,
            n_results=5000,
            where=None,
        )

        ids = result["ids"][0]
        distances = result["distances"][0]

        if not ids:
            return {
                "same_assembly": [],
                "other_assemblies": [],
                "analogs": []
            }

        # Загружаем ORM объекты
        with self._get_session() as session:
            stmt = select(ComponentDB).where(ComponentDB.unique_id.in_(ids))
            rows = session.execute(stmt).scalars().all()

        # Собираем результаты
        items = []
        for r in rows:
            if r.id == component_id:
                continue

            dist = distances[ids.index(r.unique_id)]
            similarity = 1 / (1 + dist)

            items.append({
                "id": r.id,
                "unique_id": r.unique_id,
                "component_id": r.component_id,
                "clean_name": r.clean_name,
                "vendor": r.vendor,
                "material": r.material,
                "size": r.size,
                "standard": r.standard,
                "abs_level": r.abs_level,
                "path": r.path,
                "similarity": similarity,
            })

        # Сортировка по similarity
        items.sort(key=lambda x: x["similarity"], reverse=True)

        # Категоризация
        same_assembly = []
        other_assemblies = []

        for item in items:
            # Фильтр по уровню
            if same_level_only and item["abs_level"] != obj.abs_level:
                continue

            # Дубликаты в той же сборке
            if item["component_id"] == obj.component_id and item["path"] == obj.path:
                same_assembly.append(item)
                continue

            # Дубликаты в других сборках
            if item["component_id"] == obj.component_id and item["path"] != obj.path:
                other_assemblies.append(item)
                continue

        # Формируем список аналогов
        analogs_raw = [
            item for item in items
            if item["clean_name"] != obj.clean_name
        ]

        # Убираем дубликаты по component_id
        unique_ids = set()
        analogs_unique = []

        for item in analogs_raw:
            cid = item["component_id"]
            if cid not in unique_ids:
                unique_ids.add(cid)
                analogs_unique.append(item)

        # Гарантируем минимум десять аналогов
        analogs = analogs_unique[:max(10, top_k)]

        # Ограничения
        same_assembly = same_assembly[:top_k]
        other_assemblies = other_assemblies[:top_k]

        return {
            "same_assembly": same_assembly,
            "other_assemblies": other_assemblies,
            "analogs": analogs
        }
