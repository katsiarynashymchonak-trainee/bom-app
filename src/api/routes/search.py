# src/api/routes/search.py

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any

from src.core.hybrid_search import HybridSearchService
from src.ml.embedding_service import EmbeddingService

router = APIRouter(prefix="/search", tags=["search"])

search_service = HybridSearchService()
embedder = EmbeddingService.instance()


class SearchRequest(BaseModel):
    query_text: str
    top_k: int = 20
    filters: Optional[Dict[str, Any]] = None


@router.post("/vector")
def vector_search(payload: SearchRequest):
    embedding = embedder.encode(payload.query_text)

    df = search_service.search(
        query_embedding=embedding,
        n_results=payload.top_k,
        filters=payload.filters,
    )

    return df.to_dict(orient="records")
