# src/api/routes/cross_matching.py

from fastapi import APIRouter, Query
from src.core.cross_matching import CrossMatchingService

router = APIRouter(prefix="/cross-matching", tags=["cross-matching"])

service = CrossMatchingService()


@router.get("/{component_id}")
def similar_components(
    component_id: int,
    top_k: int = Query(10, ge=1, le=100),
):
    df = service.find_similar_by_id(
        component_id=component_id,
        top_k=top_k,
    )
    return df.to_dict(orient="records")
