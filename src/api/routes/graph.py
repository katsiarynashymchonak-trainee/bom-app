# src/routes/graph.py
from fastapi import APIRouter
from src.core.graph_service import GraphService

router = APIRouter(prefix="/graph", tags=["graph"])

@router.get("")
def get_graph(max_depth: int = 3, root_id: str | None = None):
    service = GraphService.instance()
    return service.build_graph(
        max_depth=max_depth,
        root_id=root_id
    )

