from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any

from src.core.models import ComponentCreate, ComponentUpdate, ComponentRead
from src.core.component_service import ComponentService

router = APIRouter(prefix="/components", tags=["components"])

service = ComponentService()


@router.post("", response_model=ComponentRead)
def create_component(payload: ComponentCreate):
    return service.create_component(payload)


@router.get("/{component_id}", response_model=ComponentRead)
def get_component(component_id: int):
    result = service.get_component(component_id)
    if not result:
        raise HTTPException(status_code=404, detail="Component not found")
    return result


@router.patch("/{component_id}", response_model=ComponentRead)
def update_component(component_id: int, payload: ComponentUpdate):
    result = service.update_component(component_id, payload)
    if not result:
        raise HTTPException(status_code=404, detail="Component not found")
    return result


@router.delete("/{component_id}")
def delete_component(component_id: int):
    ok = service.delete_component(component_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Component not found")
    return {"deleted": True}


@router.get("", response_model=List[ComponentRead])
def list_components(
    limit: int = Query(100, ge=1, le=1_000_000),
    offset: int = Query(0, ge=0),

    # фильтры
    material_id: Optional[str] = None,
    component_id: Optional[str] = None,
    record_type: Optional[str] = None,
    abs_level: Optional[int] = None,
    is_assembly: Optional[bool] = None,
    is_subassembly: Optional[bool] = None,
    is_leaf: Optional[bool] = None,
):
    filters: Dict[str, Any] = {}

    if material_id:
        filters["material_id"] = material_id
    if component_id:
        filters["component_id"] = component_id
    if record_type:
        filters["record_type"] = record_type
    if abs_level is not None:
        filters["abs_level"] = abs_level
    if is_assembly is not None:
        filters["is_assembly"] = is_assembly
    if is_subassembly is not None:
        filters["is_subassembly"] = is_subassembly
    if is_leaf is not None:
        filters["is_leaf"] = is_leaf

    return service.list_components(
        limit=limit,
        offset=offset,
        filters=filters or None,
    )
