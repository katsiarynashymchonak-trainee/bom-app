# src/core/cross_matching.py

from typing import Dict, Any, Optional, List

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.database import SessionLocal
from src.db.models import ComponentDB
from src.core.chroma_repository import ChromaRepository
from src.ml.embedding_service import EmbeddingService


# Сервис поиска похожих компонентов по эмбеддингам
class CrossMatchingService:

    def __init__(self):
        self.chroma = ChromaRepository.instance()
        self.embedder = EmbeddingService.instance()

    # получение сессии БД
    def _get_session(self) -> Session:
        return SessionLocal()

    # получение ORM объекта компонента
    def _get_component(self, component_id: int) -> Optional[ComponentDB]:
        with self._get_session() as session:
            return session.get(ComponentDB, component_id)

    # основной метод поиска похожих компонентов
    def find_similar(
        self,
        component_id: int,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:

        obj = self._get_component(component_id)
        if not obj or not obj.embedding_vector:
            return []

        query_emb = obj.embedding_vector

        # запрашиваем много кандидатов чтобы хватило уникальных component_id
        result = self.chroma.query(
            query_embedding=query_emb,
            n_results=top_k * 1000,
            where=None,
        )

        ids = result["ids"][0]
        distances = result["distances"][0]

        if not ids:
            return []

        # загрузка ORM объектов по unique_id
        with self._get_session() as session:
            stmt = select(ComponentDB).where(ComponentDB.unique_id.in_(ids))
            rows = session.execute(stmt).scalars().all()

        # сбор результатов
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
                "is_assembly": r.is_assembly,
                "is_subassembly": r.is_subassembly,
                "is_leaf": r.is_leaf,
                "similarity": similarity,
            })

        # сортировка по similarity
        items.sort(key=lambda x: x["similarity"], reverse=True)

        # выбираем ровно top_k уникальных component_id
        seen = set()
        out = []

        for item in items:
            cid = item["component_id"]
            if cid not in seen:
                seen.add(cid)
                out.append(item)
            if len(out) == top_k:
                break

        return out
