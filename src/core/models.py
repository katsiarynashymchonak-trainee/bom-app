from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

import pandas as pd
from pydantic import BaseModel

@dataclass
class Component:
    """Доменная модель компонента сборки (в терминах данных)."""

    material_id: str
    component_id: str
    description: str
    qty: float
    level: int
    path: str

    # Извлечённые признаки
    clean_name: str = ""
    vendor: str = ""
    material: str = ""
    size: str = ""
    component_type: str = ""
    standard: str = ""

    # Иерархия и вычисленные поля
    abs_level: int = 0
    is_assembly: bool = False
    is_subassembly: bool = False
    is_leaf: bool = False

    usage_count: int = 0
    parent_id: Optional[str] = None

    # ASSEMBLY / SUBASSEMBLY / LEAF
    record_type: str = ""

    unique_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь (для БД / API / DataFrame)."""
        return {
            "material_id": self.material_id,
            "component_id": self.component_id,
            "description": self.description,
            "qty": self.qty,
            "level": self.level,
            "path": self.path,

            "clean_name": self.clean_name,
            "vendor": self.vendor,
            "material": self.material,
            "size": self.size,
            "component_type": self.component_type,
            "standard": self.standard,

            "abs_level": self.abs_level,
            "is_assembly": self.is_assembly,
            "is_subassembly": self.is_subassembly,
            "is_leaf": self.is_leaf,

            "usage_count": self.usage_count,
            "parent_id": self.parent_id,
            "record_type": self.record_type,
            "unique_id": self.unique_id,
        }


@dataclass
class HierarchyNode:
    """Узел иерархии (для построения дерева в памяти / UI)."""

    node_id: str
    name: str
    level: int
    parent_id: Optional[str] = None
    children: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_child(self, child_id: str):
        if child_id not in self.children:
            self.children.append(child_id)


@dataclass
class ProcessingResult:
    """Результат оффлайн‑обработки данных (пайплайн)."""

    success: bool
    message: str
    data: Optional[pd.DataFrame] = None
    stats: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


class ComponentBase(BaseModel):
    material_id: str
    component_id: str
    description: str
    qty: float
    path: str

    clean_name: str | None = None
    vendor: str | None = None
    material: str | None = None
    size: str | None = None
    component_type: str | None = None
    standard: str | None = None

    abs_level: int | None = None

    # новые флаги
    is_assembly: bool | None = None
    is_subassembly: bool | None = None
    is_leaf: bool | None = None

    usage_count: int | None = None
    parent_id: str | None = None

    # ASSEMBLY / SUBASSEMBLY / LEAF
    record_type: str | None = None

    unique_id: str | None = None


class ComponentCreate(ComponentBase):
    """Модель для создания компонента через API."""
    pass


class ComponentUpdate(BaseModel):
    """Модель для частичного обновления компонента через API."""

    description: str | None = None
    qty: float | None = None

    clean_name: str | None = None
    vendor: str | None = None
    material: str | None = None
    size: str | None = None
    component_type: str | None = None
    standard: str | None = None

    parent_id: str | None = None
    record_type: str | None = None

    is_assembly: bool | None = None
    is_subassembly: bool | None = None
    is_leaf: bool | None = None


class ComponentRead(ComponentBase):
    """Модель для отдачи компонента наружу через API."""
    id: int
