# src/db/models.py
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    Text,
)
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON

from src.db.database import Base


class ComponentDB(Base):
    """
    Табличная модель компонента в SQLite.
    Хранит иерархию, признаки и эмбеддинг.
    """

    __tablename__ = "components"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    unique_id = Column(String, unique=True, index=True, nullable=False)

    # Исходные поля
    material_id = Column(String, index=True, nullable=False)
    component_id = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=False)
    qty = Column(Float, nullable=False, default=1.0)
    path = Column(String, index=True, nullable=False)

    # Иерархия
    parent_id = Column(String, index=True, nullable=True)
    abs_level = Column(Integer, index=True, nullable=True)

    # Тип узла
    record_type = Column(String, index=True, nullable=True)  # ASSEMBLY / SUBASSEMBLY / LEAF
    is_assembly = Column(Boolean, default=False)
    is_subassembly = Column(Boolean, default=False)
    is_leaf = Column(Boolean, default=False)

    usage_count = Column(Integer, default=0)

    # Извлечённые признаки
    clean_name = Column(String, nullable=True)
    vendor = Column(String, index=True, nullable=True)
    material = Column(String, index=True, nullable=True)
    size = Column(String, index=True, nullable=True)
    component_type = Column(String, index=True, nullable=True)
    standard = Column(String, index=True, nullable=True)

    # Эмбеддинг
    embedding_vector = Column(SQLiteJSON, nullable=True)
