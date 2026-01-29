from fastapi import APIRouter
from src.core.component_service import ComponentService

router = APIRouter(prefix="/embeddings", tags=["embeddings"])

service = ComponentService()

@router.get("")
def get_embeddings():
    return service.list_embeddings()
