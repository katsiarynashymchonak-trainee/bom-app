import logging
import time
import threading
from typing import Dict, List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import select, func

from src.db.database import SessionLocal
from src.db.models import ComponentDB

logger = logging.getLogger(__name__)


# Сервис построения графа иерархии компонентов
class GraphService:
    _instance = None
    _lock = threading.Lock()

    # кэш по material_id
    # структура
    # { material_id: { "nodes": {id: node_dict}, "children": {pid: [cid]}, "roots": [ids] } }
    _cache_by_material: Dict[str, Dict] = {}

    _cache_hash: Optional[str] = None

    def __init__(self):
        logger.info("[Graph] GraphService initialized")

    @classmethod
    def instance(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    # публичный API
    def build_graph(self, max_depth: int = 3, root_id: Optional[str] = None) -> Dict:
        start_total = time.time()

        with SessionLocal() as session:
            db_hash = self._compute_db_hash(session)

        # сброс кэша если БД изменилась
        if self._cache_hash != db_hash:
            self._cache_by_material = {}
            self._cache_hash = db_hash

        if not root_id:
            return {"nodes": [], "edges": []}

        material_id = str(root_id)

        # построение полного графа если нет в кэше
        if material_id not in self._cache_by_material:
            self._cache_by_material[material_id] = self._build_full_graph_for_material(material_id)

        full_graph = self._cache_by_material[material_id]

        nodes, edges = self._bfs_limited(full_graph, max_depth)

        return {"nodes": nodes, "edges": edges}

    def rebuild_graph_cache(self):
        self._cache_by_material = {}
        self._cache_hash = None
        return {"status": "cache cleared"}

    # построение полного графа для одного material_id
    def _build_full_graph_for_material(self, material_id: str) -> Dict:
        with SessionLocal() as session:
            rows = session.execute(select(ComponentDB)).scalars().all()

        material_rows = [r for r in rows if r.material_id == material_id]

        if not material_rows:
            return {"nodes": {}, "children": {}, "roots": []}

        nodes = {str(r.id): self._node_to_dict(r) for r in material_rows}

        children: Dict[str, List[str]] = {}
        roots = []

        for r in material_rows:
            pid = str(r.parent_id) if r.parent_id is not None else None
            cid = str(r.id)

            if pid is None:
                roots.append(cid)
            else:
                children.setdefault(pid, []).append(cid)

        logger.info(f"[Graph][DEBUG] Material {material_id}: total nodes={len(nodes)}")
        logger.info(f"[Graph][DEBUG] Roots: {roots}")

        for pid, child_ids in children.items():
            logger.info(f"[Graph][DEBUG] parent_id={pid} → children={child_ids}")

        for nid, nd in nodes.items():
            if nd.get("is_subassembly"):
                logger.info(
                    f"[Graph][DEBUG] SUBASSEMBLY {nid}: clean_name={nd.get('clean_name')}, children={children.get(nid)}"
                )

        return {
            "nodes": nodes,
            "children": children,
            "roots": roots,
        }

    # ограниченный BFS по кэшированному графу
    def _bfs_limited(self, full_graph: Dict, max_depth: int):
        nodes_dict = full_graph["nodes"]
        children_map = full_graph["children"]
        roots = full_graph["roots"]

        if not roots:
            return [], []

        queue = [(rid, 0) for rid in roots]
        visited = set()

        out_nodes = []
        out_edges = []

        MAX_NODES = 2000

        while queue:
            node_id, depth = queue.pop(0)

            if node_id in visited:
                continue
            visited.add(node_id)

            out_nodes.append(nodes_dict[node_id])

            if len(out_nodes) >= MAX_NODES:
                break

            if depth >= max_depth:
                continue

            for child_id in children_map.get(node_id, []):
                out_edges.append({"source": node_id, "target": child_id})
                queue.append((child_id, depth + 1))

        return out_nodes, out_edges

    # вычисление хэша БД для инвалидации кэша
    def _compute_db_hash(self, session: Session) -> str:
        count = session.execute(select(func.count(ComponentDB.id))).scalar()
        max_update = session.execute(select(func.max(ComponentDB.updated_at))).scalar()
        return f"{count}-{max_update}"

    # сериализация узла графа
    def _node_to_dict(self, r: ComponentDB) -> Dict:
        return {
            "id": r.id,
            "component_id": r.component_id,
            "clean_name": r.clean_name,
            "abs_level": r.abs_level,
            "path": r.path,
            "parent_id": r.parent_id,
            "usage_count": r.usage_count,

            "is_assembly": r.is_assembly,
            "is_subassembly": r.is_subassembly,
            "is_leaf": r.is_leaf,

            "material": r.material,
            "vendor": r.vendor,
            "size": r.size,
            "standard": r.standard,
        }
