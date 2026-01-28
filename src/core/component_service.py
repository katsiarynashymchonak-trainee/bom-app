from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import select, func

from src.db.database import SessionLocal
from src.db.models import ComponentDB
from src.core.chroma_repository import ChromaRepository
from src.ml.embedding_service import EmbeddingService
from src.core.models import ComponentCreate, ComponentUpdate, ComponentRead


# Сервисный слой для работы с компонентами
class ComponentService:

    def __init__(self):
        self.chroma = ChromaRepository.instance()
        self.embedder = EmbeddingService.instance()

    # получение сессии БД
    def _get_session(self) -> Session:
        return SessionLocal()

    # преобразование ORM объекта в модель ответа
    def _to_read_model(self, obj: ComponentDB) -> ComponentRead:
        return ComponentRead(
            id=obj.id,
            unique_id=obj.unique_id,

            material_id=obj.material_id,
            component_id=obj.component_id,
            qty=obj.qty,
            path=obj.path,

            clean_name=obj.clean_name,
            vendor=obj.vendor,
            material=obj.material,
            size=obj.size,
            component_type=obj.component_type,
            standard=obj.standard,

            abs_level=obj.abs_level,
            is_assembly=obj.is_assembly,
            is_subassembly=obj.is_subassembly,
            is_leaf=obj.is_leaf,

            usage_count=obj.usage_count,
            parent_id=obj.parent_id,
        )

    # работа с эмбеддингами и Chroma
    def _ensure_embedding(self, obj: ComponentDB) -> None:
        if not obj.embedding_vector:
            text = obj.clean_name or ""
            obj.embedding_vector = self.embedder.encode(text)

    def _upsert_chroma(self, obj: ComponentDB) -> None:
        if not obj.embedding_vector:
            return

        self.chroma.upsert(
            ids=[str(obj.unique_id)],
            embeddings=[obj.embedding_vector],
            metadatas=[
                {
                    "component_id": obj.component_id,
                    "material_id": obj.material_id,
                    "abs_level": obj.abs_level,
                    "is_assembly": obj.is_assembly,
                    "is_subassembly": obj.is_subassembly,
                    "is_leaf": obj.is_leaf,
                }
            ],
        )

    def _delete_from_chroma(self, unique_id: str) -> None:
        self.chroma.delete(ids=[str(unique_id)])

    # CRUD операции
    def create_component(self, data: ComponentCreate) -> ComponentRead:
        with self._get_session() as session:
            obj = ComponentDB(
                unique_id=data.unique_id or f"{data.material_id}:{data.component_id}:{data.path}",

                material_id=data.material_id,
                component_id=data.component_id,
                qty=data.qty,
                path=data.path,

                clean_name=data.clean_name or "",
                vendor=data.vendor,
                material=data.material,
                size=data.size,
                component_type=data.component_type,
                standard=data.standard,

                abs_level=data.abs_level or 0,
                is_assembly=bool(data.is_assembly) if data.is_assembly is not None else False,
                is_subassembly=bool(data.is_subassembly) if data.is_subassembly is not None else False,
                is_leaf=bool(data.is_leaf) if data.is_leaf is not None else False,

                usage_count=data.usage_count or 0,
                parent_id=data.parent_id,
            )

            self._ensure_embedding(obj)
            session.add(obj)
            session.commit()
            session.refresh(obj)

            self._upsert_chroma(obj)

            return self._to_read_model(obj)

    def get_component(self, component_id: int) -> Optional[ComponentRead]:
        with self._get_session() as session:
            obj = session.get(ComponentDB, component_id)
            return self._to_read_model(obj) if obj else None

    def get_component_by_unique_id(self, unique_id: str) -> Optional[ComponentRead]:
        with self._get_session() as session:
            stmt = select(ComponentDB).where(ComponentDB.unique_id == unique_id)
            obj = session.execute(stmt).scalar_one_or_none()
            return self._to_read_model(obj) if obj else None

    def update_component(self, component_id: int, updates: ComponentUpdate) -> Optional[ComponentRead]:
        with self._get_session() as session:
            obj = session.get(ComponentDB, component_id)
            if not obj:
                return None

            data = updates.dict(exclude_unset=True)

            forbidden = {"thread_info", "grade", "finish"}
            for f in forbidden:
                data.pop(f, None)

            for k, v in data.items():
                setattr(obj, k, v)

            if "clean_name" in data:
                self._ensure_embedding(obj)

            session.add(obj)
            session.commit()
            session.refresh(obj)

            self._upsert_chroma(obj)

            return self._to_read_model(obj)

    def delete_component(self, component_id: int) -> bool:
        with self._get_session() as session:
            obj = session.get(ComponentDB, component_id)
            if not obj:
                return False

            base_path = obj.path

            stmt = select(ComponentDB).where(ComponentDB.path.like(f"{base_path}.%"))
            children = session.execute(stmt).scalars().all()

            for child in children:
                if child.unique_id:
                    self._delete_from_chroma(child.unique_id)

            for child in children:
                session.delete(child)

            if obj.unique_id:
                self._delete_from_chroma(obj.unique_id)

            session.delete(obj)
            session.commit()
            return True

    # выборка и статистика
    def list_components(self, limit: int = 100, offset: int = 0, filters: Optional[Dict[str, Any]] = None) -> List[ComponentRead]:
        with self._get_session() as session:
            stmt = select(ComponentDB)

            if filters:
                if "material_id" in filters:
                    stmt = stmt.where(ComponentDB.material_id == filters["material_id"])
                if "component_id" in filters:
                    stmt = stmt.where(ComponentDB.component_id == filters["component_id"])
                if "abs_level" in filters:
                    stmt = stmt.where(ComponentDB.abs_level == filters["abs_level"])
                if "is_assembly" in filters:
                    stmt = stmt.where(ComponentDB.is_assembly == filters["is_assembly"])
                if "is_subassembly" in filters:
                    stmt = stmt.where(ComponentDB.is_subassembly == filters["is_subassembly"])
                if "is_leaf" in filters:
                    stmt = stmt.where(ComponentDB.is_leaf == filters["is_leaf"])

            stmt = stmt.offset(offset).limit(limit)
            rows = session.execute(stmt).scalars().all()

            return [self._to_read_model(r) for r in rows]

    def get_global_stats(self) -> Dict[str, Any]:
        with self._get_session() as session:
            total = session.query(func.count(ComponentDB.id)).scalar() or 0

            assemblies = session.query(func.count(ComponentDB.id)).filter(ComponentDB.is_assembly == True).scalar() or 0
            subassemblies = session.query(func.count(ComponentDB.id)).filter(ComponentDB.is_subassembly == True).scalar() or 0
            leafs = session.query(func.count(ComponentDB.id)).filter(ComponentDB.is_leaf == True).scalar() or 0

            max_depth = session.query(func.max(ComponentDB.abs_level)).scalar()
            max_depth = int(max_depth) if max_depth is not None else 0

            unique_materials = session.query(func.count(func.distinct(ComponentDB.material))).scalar() or 0
            unique_vendors = session.query(func.count(func.distinct(ComponentDB.vendor))).scalar() or 0
            unique_types = session.query(func.count(func.distinct(ComponentDB.component_type))).scalar() or 0

        return {
            "total": int(total),
            "assemblies": int(assemblies),
            "subassemblies": int(subassemblies),
            "leafs": int(leafs),
            "max_depth": max_depth,
            "unique_materials": int(unique_materials),
            "unique_vendors": int(unique_vendors),
            "unique_types": int(unique_types),
        }

    def list_material_ids(self) -> List[str]:
        with self._get_session() as session:
            stmt = select(func.distinct(ComponentDB.material_id))
            rows = session.execute(stmt).scalars().all()

        return sorted([m for m in rows if m])

    def search_components(self, query: str, column: Optional[str] = None, record_types: Optional[List[str]] = None):
        with self._get_session() as session:
            stmt = select(ComponentDB)
            rows = session.execute(stmt).scalars().all()

            q = query.lower()
            result = []

            for r in rows:
                if column:
                    value = getattr(r, column, None)
                    if value is None:
                        continue
                    if q not in str(value).lower():
                        continue
                else:
                    if q not in str(r.component_id).lower() and q not in str(r.clean_name).lower():
                        continue

                if record_types and r.record_type not in record_types:
                    continue

                result.append(r)

            return [self._to_read_model(r) for r in result]

    def list_vendors(self) -> List[str]:
        with self._get_session() as session:
            stmt = select(func.distinct(ComponentDB.vendor))
            rows = session.execute(stmt).scalars().all()

        return sorted([v for v in rows if v])


# поиск похожих компонентов по эмбеддингам
def get_similar_components(self, component_id: int, limit: int = 10):
    with self._get_session() as session:
        obj = session.get(ComponentDB, component_id)
        if not obj or not obj.embedding_vector:
            return []

        query_emb = obj.embedding_vector

        result = self.chroma.query(
            query_embedding=query_emb,
            n_results=limit + 1,
            where=None
        )

        ids = result["ids"][0]
        distances = result["distances"][0]

        stmt = select(ComponentDB).where(ComponentDB.unique_id.in_(ids))
        rows = session.execute(stmt).scalars().all()

        out = []
        for r in rows:
            if r.id == component_id:
                continue

            dist = distances[ids.index(r.unique_id)]
            out.append({
                "id": r.id,
                "component_id": r.component_id,
                "clean_name": r.clean_name,
                "vendor": r.vendor,
                "material": r.material,
                "size": r.size,
                "standard": r.standard,
                "similarity": 1 / (1 + dist)
            })

        out.sort(key=lambda x: x["similarity"], reverse=True)

        return out[:limit]
