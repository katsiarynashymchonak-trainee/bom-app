import pandas as pd
from typing import List, Dict, Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.database import SessionLocal
from src.db.models import ComponentDB
from src.core.chroma_repository import ChromaRepository


class HybridSearchService:
    """
    Гибридный поиск:
    - векторный поиск через ChromaDB
    - фильтрация по признакам из SQLite
    """

    def __init__(self):
        self.chroma = ChromaRepository.instance()

    def _get_session(self) -> Session:
        return SessionLocal()

    def _load_components_by_ids(self, ids: List[str]) -> pd.DataFrame:
        """
        Загружает компоненты из SQLite по списку unique_id.
        """
        if not ids:
            return pd.DataFrame()

        with self._get_session() as session:
            stmt = select(ComponentDB).where(ComponentDB.unique_id.in_(ids))
            rows = session.execute(stmt).scalars().all()

        if not rows:
            return pd.DataFrame()

        return pd.DataFrame([{
            "unique_id": r.unique_id,
            "component_id": r.component_id,
            "material_id": r.material_id,
            "record_type": r.record_type,
            "abs_level": r.abs_level,
            "clean_name": r.clean_name,
            "vendor": r.vendor,
            "material": r.material,
            "size": r.size,
            "component_type": r.component_type,
            "grade": r.grade,
            "finish": r.finish,
            "standard": r.standard,
            "path": r.path,
            "qty": r.qty,
        } for r in rows])

    def search(
        self,
        query_embedding: List[float],
        n_results: int = 20,
        filters: Optional[Dict[str, Any]] = None,
    ) -> pd.DataFrame:

        # Фильтры для Chroma (только по metadata)
        chroma_where = {}
        if filters:
            for key, value in filters.items():
                if key in ["component_id", "material_id", "record_type", "abs_level"]:
                    chroma_where[key] = value

        # Векторный поиск
        result = self.chroma.query(
            query_embedding=query_embedding,
            n_results=n_results,
            where=chroma_where or None,
        )

        ids = result.get("ids", [[]])[0]
        distances = result.get("distances", [[]])[0]

        if not ids:
            return pd.DataFrame()

        # Загружаем компоненты из SQLite
        df = self._load_components_by_ids(ids)
        if df.empty:
            return df

        # Добавляем score
        score_map = {id_: dist for id_, dist in zip(ids, distances)}
        df["score"] = df["unique_id"].map(score_map)

        # Дополнительная фильтрация по признакам
        if filters:
            for key, value in filters.items():
                if key in df.columns:
                    df = df[df[key] == value]

        return df.sort_values("score")
