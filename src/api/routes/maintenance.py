from fastapi import APIRouter, BackgroundTasks

from src.ml.embedding_service import EmbeddingService
from src.core.graph_service import GraphService

router = APIRouter(prefix="/maintenance", tags=["maintenance"])


@router.post("/rebuild_embeddings")
def rebuild_embeddings(background: BackgroundTasks):
    service = EmbeddingService.instance()
    background.add_task(service.rebuild_embeddings)
    return {"status": "started"}



@router.post("/rebuild_graph")
def rebuild_graph():
    service = GraphService.instance()
    graph = service.rebuild_graph_cache()
    return graph

