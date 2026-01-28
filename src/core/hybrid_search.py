import pandas as pd
from typing import List, Dict, Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.database import SessionLocal
from src.db.models import ComponentDB
from src.core.chroma_repository import ChromaRepository


# Гибридный поиск по эмбеддингам и фильтрам SQLite
class HybridSearchService:

    def __init__(self):
        self.chroma = ChromaRepository.instance()

    # получение сессии БД
    def _get_session(self) -> Session:
        return SessionLocal()

    # быстрая загрузка компонентов по списку unique_id
    def _load_components_by_ids(self, ids: List[str]) -> pd.DataFrame:
        if not ids:
            return pd.DataFrame()

        with self._get_session() as session:
            stmt = (
                select(
                    ComponentDB.id,
                    ComponentDB.unique_id,
                    ComponentDB.component_id,
                    ComponentDB.material_id,
                    ComponentDB.abs_level,
                    ComponentDB.clean_name,
                    ComponentDB.vendor,
                    ComponentDB.material,
                    ComponentDB.size,
                    ComponentDB.component_type,
                    ComponentDB.standard,
                    ComponentDB.path,
                    ComponentDB.qty,
                    ComponentDB.is_assembly,
                    ComponentDB.is_subassembly,
                    ComponentDB.is_leaf,
                )
                .where(ComponentDB.unique_id.in_(ids))
            )

            rows = session.execute(stmt).all()

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(
            rows,
            columns=[
                "id",
                "unique_id",
                "component_id",
                "material_id",
                "abs_level",
                "clean_name",
                "vendor",
                "material",
                "size",
                "component_type",
                "standard",
                "path",
                "qty",
                "is_assembly",
                "is_subassembly",
                "is_leaf",
            ],
        )

        return df

    # основной метод гибридного поиска
    def search(
        self,
        query_embedding: List[float],
        n_results: int = 20,
        filters: Optional[Dict[str, Any]] = None,
    ) -> pd.DataFrame:

        chroma_where: Dict[str, Any] = {}

        # построение корректного where для Chroma
        if filters:
            and_filters = []
            or_filters = []

            if "record_types" in filters:
                types = filters["record_types"]

                if "ASSEMBLY" in types:
                    or_filters.append({"is_assembly": True})
                if "SUBASSEMBLY" in types:
                    or_filters.append({"is_subassembly": True})
                if "LEAF" in types:
                    or_filters.append({"is_leaf": True})

            if "material_id" in filters:
                and_filters.append({"material_id": filters["material_id"]})

            if "vendor" in filters:
                and_filters.append({"vendor": filters["vendor"]})

            if or_filters and and_filters:
                chroma_where = {"$and": [{"$or": or_filters}, *and_filters]}

            elif or_filters:
                if len(or_filters) == 1:
                    chroma_where = or_filters[0]
                else:
                    chroma_where = {"$or": or_filters}

            elif and_filters:
                if len(and_filters) == 1:
                    chroma_where = and_filters[0]
                else:
                    chroma_where = {"$and": and_filters}

            else:
                chroma_where = {}

        # векторный поиск в Chroma с большим пулом кандидатов
        result = self.chroma.query(
            query_embedding=query_embedding,
            n_results=200,
            where=chroma_where or None,
        )

        ids = result["ids"][0] if result["ids"] else []
        distances = result["distances"][0] if result["distances"] else []

        if not ids:
            return pd.DataFrame()

        # загрузка данных из SQLite
        df = self._load_components_by_ids(ids)
        if df.empty:
            return df

        score_map = {id_: dist for id_, dist in zip(ids, distances)}
        df["score"] = df["unique_id"].map(score_map)

        # фильтрация pandas
        if filters:

            if "record_types" in filters:
                types = filters["record_types"]
                mask = False

                if "ASSEMBLY" in types:
                    mask |= df["is_assembly"] == True
                if "SUBASSEMBLY" in types:
                    mask |= df["is_subassembly"] == True
                if "LEAF" in types:
                    mask |= df["is_leaf"] == True

                df = df[mask]

            if "material_id" in filters:
                df = df[df["material_id"] == filters["material_id"]]

            if "vendor" in filters:
                df = df[df["vendor"] == filters["vendor"]]

        # сбор 10 уникальных component_id
        df = df.sort_values("score")

        seen = set()
        rows = []

        for _, row in df.iterrows():
            cid = row["component_id"]
            if cid not in seen:
                seen.add(cid)
                rows.append(row)
            if len(rows) == 10:
                break

        if not rows:
            return pd.DataFrame()

        return pd.DataFrame(rows)
