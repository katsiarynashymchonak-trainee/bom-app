from fastapi import APIRouter
from src.core.component_service import ComponentService

router = APIRouter(prefix="/stats", tags=["stats"])

# создаём один экземпляр сервиса
service = ComponentService()


@router.get("")
def get_stats():
    """
    Возвращает агрегированную статистику по базе:
    - total
    - assemblies
    - subassemblies
    - leafs
    - max_depth
    - unique_materials
    - unique_vendors
    - unique_types
    """
    return service.get_global_stats()
