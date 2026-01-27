# src/core/cross_matching.py

from typing import Dict, Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.database import SessionLocal
from src.db.models import ComponentDB
from src.core.chroma_repository import ChromaRepository
from src.core.hybrid_search import HybridSearchService


class CrossMatchingService:
    """
    Сервис для поиска похожих компонентов (cross-matching).
    """

    def __init__(self):
        self.chroma = ChromaRepository.instance()
        self.hybrid = HybridSearchService()

    def _get_session(self) -> Session:
        return SessionLocal()

    def _get_component_by_id(self, component_id: int) -> Optional[ComponentDB]:
        with self._get_session() as session:
            return session.get(ComponentDB, component_id)

    def _get_component_by_unique_id(self, unique_id: str) -> Optional[ComponentDB]:
        with self._get_session() as session:
            stmt = select(ComponentDB).where(ComponentDB.unique_id == unique_id)
            return session.execute(stmt).scalar_one_or_none()

    def find_similar_by_id(
        self,
        component_id: int,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ):
        obj = self._get_component_by_id(component_id)
        if not obj or not obj.embedding_vector:
            return []

        return self.hybrid.search(
            query_embedding=obj.embedding_vector,
            n_results=top_k,
            filters=filters,
        )

    def find_similar_by_unique_id(
        self,
        unique_id: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ):
        obj = self._get_component_by_unique_id(unique_id)
        if not obj or not obj.embedding_vector:
            return []

        return self.hybrid.search(
            query_embedding=obj.embedding_vector,
            n_results=top_k,
            filters=filters,
        )
