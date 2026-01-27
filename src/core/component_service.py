from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import select, func

from src.db.database import SessionLocal
from src.db.models import ComponentDB
from src.core.chroma_repository import ChromaRepository
from src.ml.embedding_service import EmbeddingService
from src.core.models import ComponentCreate, ComponentUpdate, ComponentRead


# Сервисный слой для работы с компонентами
# CRUD операции
# Синхронизация эмбеддингов с Chroma
# Получение агрегированной статистики
class ComponentService:

    def __init__(self):
        self.chroma = ChromaRepository.instance()  # доступ к ChromaDB
        self.embedder = EmbeddingService.instance()  # генерация эмбеддингов

    # получение сессии БД
    def _get_session(self) -> Session:
        return SessionLocal()

    # преобразование ORM объекта в модель ответа
    def _to_read_model(self, obj: ComponentDB) -> ComponentRead:
        return ComponentRead(
            id=obj.id,
            material_id=obj.material_id,
            component_id=obj.component_id,
            description=obj.description,
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
            record_type=obj.record_type,
            unique_id=obj.unique_id,
        )

    # генерация эмбеддинга при отсутствии
    def _ensure_embedding(self, obj: ComponentDB) -> None:
        if not obj.embedding_vector:
            text = obj.clean_name or obj.description or ""
            obj.embedding_vector = self.embedder.encode(text)

    # обновление или вставка записи в ChromaDB
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
                    "record_type": obj.record_type,
                    "abs_level": obj.abs_level,
                }
            ],
        )

    # удаление записи из ChromaDB
    def _delete_from_chroma(self, unique_id: str) -> None:
        self.chroma.delete(ids=[str(unique_id)])

    # создание компонента
    def create_component(self, data: ComponentCreate) -> ComponentRead:
        with self._get_session() as session:
            obj = ComponentDB(
                unique_id=data.unique_id or f"{data.material_id}:{data.component_id}:{data.path}",

                material_id=data.material_id,
                component_id=data.component_id,
                description=data.description,
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
                record_type=data.record_type or "LEAF",
            )

            self._ensure_embedding(obj)
            session.add(obj)
            session.commit()
            session.refresh(obj)

            self._upsert_chroma(obj)

            return self._to_read_model(obj)

    # получение компонента по ID
    def get_component(self, component_id: int) -> Optional[ComponentRead]:
        with self._get_session() as session:
            obj = session.get(ComponentDB, component_id)
            return self._to_read_model(obj) if obj else None

    # получение компонента по уникальному ID
    def get_component_by_unique_id(self, unique_id: str) -> Optional[ComponentRead]:
        with self._get_session() as session:
            stmt = select(ComponentDB).where(ComponentDB.unique_id == unique_id)
            obj = session.execute(stmt).scalar_one_or_none()
            return self._to_read_model(obj) if obj else None

    # обновление компонента
    def update_component(self, component_id: int, updates: ComponentUpdate) -> Optional[ComponentRead]:
        with self._get_session() as session:
            obj = session.get(ComponentDB, component_id)
            if not obj:
                return None

            data = updates.dict(exclude_unset=True)

            # удалённые поля не должны обновляться
            forbidden = {"thread_info", "grade", "finish"}
            for f in forbidden:
                data.pop(f, None)

            for k, v in data.items():
                setattr(obj, k, v)

            if "description" in data or "clean_name" in data:
                self._ensure_embedding(obj)

            session.add(obj)
            session.commit()
            session.refresh(obj)

            self._upsert_chroma(obj)

            return self._to_read_model(obj)

    # удаление компонента вместе с потомками
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

    # получение списка компонентов с фильтрами
    def list_components(
        self,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[ComponentRead]:
        with self._get_session() as session:
            stmt = select(ComponentDB)

            if filters:
                if "material_id" in filters:
                    stmt = stmt.where(ComponentDB.material_id == filters["material_id"])
                if "component_id" in filters:
                    stmt = stmt.where(ComponentDB.component_id == filters["component_id"])
                if "record_type" in filters:
                    stmt = stmt.where(ComponentDB.record_type == filters["record_type"])
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

    # агрегированная статистика по БД
    def get_global_stats(self) -> Dict[str, Any]:
        with self._get_session() as session:
            total = session.query(func.count(ComponentDB.id)).scalar() or 0

            assemblies = (
                session.query(func.count(ComponentDB.id))
                .filter(ComponentDB.record_type == "ASSEMBLY")
                .scalar()
                or 0
            )
            subassemblies = (
                session.query(func.count(ComponentDB.id))
                .filter(ComponentDB.record_type == "SUBASSEMBLY")
                .scalar()
                or 0
            )
            leafs = (
                session.query(func.count(ComponentDB.id))
                .filter(ComponentDB.record_type == "LEAF")
                .scalar()
                or 0
            )

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
