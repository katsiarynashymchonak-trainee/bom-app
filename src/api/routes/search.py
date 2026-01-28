from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from src.core.hybrid_search import HybridSearchService
from src.ml.embedding_service import EmbeddingService
from src.core.component_service import ComponentService
from src.core.models import ComponentRead

router = APIRouter(prefix="/search", tags=["search"])

search_service = HybridSearchService()
embedder = EmbeddingService.instance()
component_service = ComponentService()


class SearchRequest(BaseModel):
    query_text: str
    top_k: int = 1000
    filters: Optional[Dict[str, Any]] = None


class ComponentTextSearch(BaseModel):
    query: str
    column: Optional[str] = None
    limit: int = 1000
    record_types: Optional[List[str]] = None


@router.post("/components", response_model=List[ComponentRead])
def text_search_components(payload: ComponentTextSearch):
    results = component_service.search_components(
        query=payload.query.lower(),
        column=payload.column,
        record_types=payload.record_types,
    )
    return results[: payload.limit]

class HybridSearchRequest(BaseModel):
    query: str
    top_k: int = 50
    record_types: Optional[List[str]] = None
    material_id: Optional[str] = None
    vendor: Optional[str] = None



@router.post("/hybrid")
def hybrid_search(payload: HybridSearchRequest):
    embedding = embedder.encode(payload.query)

    filters: Dict[str, Any] = {}

    if payload.record_types:
        filters["record_types"] = payload.record_types

    if payload.material_id:
        filters["material_id"] = payload.material_id

    if payload.vendor:
        filters["vendor"] = payload.vendor

    df = search_service.search(
        query_embedding=embedding,
        n_results=payload.top_k,
        filters=filters or None,
    )

    return df.to_dict(orient="records")



