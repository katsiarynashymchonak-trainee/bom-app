import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config
import requests

from src.utils.api_client import (
    api_get_graph,
    api_get_component,
    api_get_similar_components,
    api_get_material_ids,
    api_hybrid_search,
    api_get_vendors,
)

# кэширование списков
@st.cache_data
def _load_material_ids():
    try:
        return api_get_material_ids()
    except Exception:
        return []


@st.cache_data
def _load_vendors():
    try:
        return api_get_vendors()
    except Exception:
        return []


@st.cache_data(show_spinner=False)
def _load_graph(root_id, max_depth):
    return api_get_graph(root_id=root_id, max_depth=max_depth)


@st.cache_data
def _load_component(cid):
    return api_get_component(cid)


def _load_similar(cid, limit):
    return api_get_similar_components(cid, limit)


# построение элементов графа
def _build_graph_elements(graph_data, search_query: str | None = None):
    nodes_raw = graph_data.get("nodes", [])
    edges_raw = graph_data.get("edges", [])

    search_query = (search_query or "").strip().lower()
    highlight_ids = set()

    if search_query:
        for n in nodes_raw:
            label = str(n.get("clean_name", "")).lower()
            cid = str(n.get("component_id", "")).lower()
            if search_query in label or search_query in cid:
                highlight_ids.add(str(n["id"]))

    nodes = []
    for n in nodes_raw:
        node_id = str(n["id"])

        if n.get("is_assembly"):
            record_type = "ASSEMBLY"
        elif n.get("is_subassembly"):
            record_type = "SUBASSEMBLY"
        elif n.get("is_leaf"):
            record_type = "LEAF"
        else:
            record_type = "UNKNOWN"

        label = n.get("component_id") or node_id
        level = int(n.get("abs_level", 0))

        clean_title = n.get("clean_name") or n.get("component_id") or label
        title = f"{clean_title} (level {level}, {record_type})"

        if record_type == "ASSEMBLY":
            color = "#1D4ED8"
        elif record_type == "SUBASSEMBLY":
            color = "#10B981"
        elif record_type == "LEAF":
            color = "#6B7280"
        else:
            color = "#4F46E5"

        if node_id in highlight_ids:
            color = "#F97316"

        nodes.append(
            Node(
                id=node_id,
                label=label,
                size=15 + level * 2,
                color=color,
                title=title,
            )
        )

    edges = [
        Edge(
            source=str(e["source"]),
            target=str(e["target"]),
            color="#9CA3AF",
        )
        for e in edges_raw
    ]

    return nodes, edges


# блок управления графом
def _render_controls():
    st.markdown("### Graph Controls")

    material_ids = _load_material_ids()

    if material_ids:
        current_root = st.session_state.graph_root or material_ids[0]
        if current_root not in material_ids:
            current_root = material_ids[0]

        root_query = st.selectbox(
            "Root material",
            material_ids,
            index=material_ids.index(current_root),
        )
    else:
        root_query = st.text_input(
            "Root ID (no material_ids available)",
            value=st.session_state.graph_root or "",
        )

    st.session_state.graph_root = root_query
    max_depth = st.slider("Depth level", 1, 9, 3)

    if st.button("Build graph"):
        if not st.session_state.graph_root:
            st.warning("Set root first")
        else:
            st.session_state.node_cache = {}
            st.session_state.graph_data = _load_graph(
                st.session_state.graph_root,
                max_depth,
            )
            st.session_state.selected_node_id = None

    return root_query, max_depth


# поиск и гибридный поиск
def _render_search_and_hybrid():
    st.markdown("### Search in graph")
    search_query = st.text_input("Search by ID or name", value="")

    st.markdown("---")
    st.markdown("### Hybrid search (vector + filters)")

    hybrid_query = st.text_input("Search query", key="hybrid_query")

    record_type_filter = st.multiselect(
        "Record type filter",
        ["ASSEMBLY", "SUBASSEMBLY", "LEAF"],
    )

    try:
        vendors = _load_vendors()
    except Exception:
        vendors = []

    vendor_filter = None
    if vendors:
        vendor_filter = st.selectbox(
            "Vendor filter (optional)",
            [""] + vendors,
            index=0,
            key="vendor_filter",
        )
        if vendor_filter == "":
            vendor_filter = None

    material_ids = _load_material_ids()
    material_filter = None
    if material_ids:
        material_filter = st.selectbox(
            "Material ID filter (optional)",
            [""] + material_ids,
            index=0,
            key="material_filter",
        )
        if material_filter == "":
            material_filter = None

    if st.button("Run hybrid search"):
        hybrid_results = api_hybrid_search(
            query=hybrid_query,
            record_types=record_type_filter,
            material_id=material_filter,
            vendor=vendor_filter,
            top_k=20,
        )

        if not hybrid_results:
            st.warning("No components found for this query.")
        else:
            st.session_state.hybrid_results = hybrid_results

    if st.session_state.get("hybrid_results"):
        st.markdown("**Search results:**")

        for comp in st.session_state.hybrid_results:
            score = comp.get("score")
            score_str = f" (score={round(score, 4)})" if score is not None else ""

            if st.button(
                f"{comp['component_id']} — {comp.get('clean_name', '')}{score_str}",
                key=f"hybrid_result_{comp['unique_id']}",
            ):
                st.session_state.selected_node_id = comp["id"]
                st.session_state.node_cache = {}
                st.session_state.similar_results = None
                st.rerun()

    return search_query


# блок обслуживания
def _render_maintenance():
    st.markdown("---")
    st.markdown("### Maintenance")

    if st.button("Rebuild embeddings"):
        r = requests.post("http://localhost:8000/maintenance/rebuild_embeddings")
        st.json(r.json())

    if st.button("Rebuild graph cache"):
        r = requests.post("http://localhost:8000/maintenance/rebuild_graph")
        st.session_state.graph_data = None
        st.json(r.json())


# детали выбранного узла
def _render_node_details():
    st.markdown("---")
    st.markdown("### Node details")

    if "node_cache" not in st.session_state:
        st.session_state.node_cache = {}

    node_id = st.session_state.selected_node_id
    if not node_id:
        st.info("Click on a node in the graph to see details.")
        return

    # загрузка компонента
    if node_id in st.session_state.node_cache:
        component = st.session_state.node_cache[node_id]
    else:
        component = _load_component(node_id)
        if not component:
            st.warning("Component not found.")
            return
        st.session_state.node_cache[node_id] = component

    # определение типа записи
    if component.get("is_assembly"):
        record_type = "ASSEMBLY"
    elif component.get("is_subassembly"):
        record_type = "SUBASSEMBLY"
    elif component.get("is_leaf"):
        record_type = "LEAF"
    else:
        record_type = "UNKNOWN"

    col_info, col_similar = st.columns([2, 1])

    with col_info:
        st.markdown(f"**Unique ID:** `{component.get('unique_id', '')}`")
        st.markdown(f"**Material ID:** {component.get('material_id', '')}")
        st.markdown(f"**Component ID:** {component.get('component_id', '')}")
        st.markdown(f"**Clean name:** {component.get('clean_name', '')}")
        st.markdown(f"**Record type:** {record_type}")
        st.markdown(f"**Component type:** {component.get('component_type', '')}")
        st.markdown(f"**Path:** `{component.get('path', '')}`")
        st.markdown(f"**Level:** {component.get('abs_level', '')}")
        st.markdown(f"**Usage count:** {component.get('usage_count', '')}")
        st.markdown(f"**Vendor:** {component.get('vendor', '')}")
        st.markdown(f"**Material:** {component.get('material', '')}")
        st.markdown(f"**Size:** {component.get('size', '')}")
        st.markdown(f"**Standard:** {component.get('standard', '')}")

    with col_similar:
        st.markdown("**Similar components (cross-matching)**")

        same_level_only = st.checkbox("Same level only", value=False)

        if st.button("Find similar components"):
            st.session_state.similar_results = None

            results = api_get_similar_components(
                component["id"],
                limit=10,
                same_level_only=same_level_only,
            )

            st.session_state.similar_results = results

            if not results or (
                not results.get("same_assembly")
                and not results.get("other_assemblies")
                and not results.get("analogs")
            ):
                st.warning("No similar components found")
                st.stop()

            st.rerun()

        results = st.session_state.get("similar_results", {})

        if not results:
            return

        def _render_match_button(s, prefix: str):
            label = (
                f"{s['component_id']} — {s.get('clean_name', '')} "
                f"(material {s.get('material', '')} sim {round(s['similarity'], 3)})"
            )
            if st.button(label, key=f"{prefix}_{s['id']}"):
                if st.session_state.selected_node_id != s["id"]:
                    st.session_state.selected_node_id = s["id"]
                    st.session_state.node_cache.pop(s["id"], None)
                    st.rerun()

        # Same assembly
        same_assembly = results.get("same_assembly", [])
        if same_assembly:
            st.markdown("#### Same assembly")
            for s in same_assembly:
                _render_match_button(s, "same")

        # Other assemblies
        other_assemblies = results.get("other_assemblies", [])
        if other_assemblies:
            st.markdown("#### Other assemblies")
            for s in other_assemblies:
                _render_match_button(s, "other")

        # Analogs
        analogs = results.get("analogs", [])
        if analogs:
            st.markdown("#### Analogs different clean name")
            for s in analogs:
                _render_match_button(s, "analog")


# отображение графа
def _render_graph_area(search_query):
    st.markdown("### Hierarchical Graph View")

    if st.session_state.graph_data is None:
        st.info("Select root and click 'Build graph' to generate the assembly graph.")
        return

    nodes_raw = st.session_state.graph_data.get("nodes", [])
    edges_raw = st.session_state.graph_data.get("edges", [])

    if len(nodes_raw) > 2000:
        st.warning(f"Graph too large ({len(nodes_raw)} nodes). Showing first 2000.")
        nodes_raw = nodes_raw[:2000]
        node_ids = {str(n["id"]) for n in nodes_raw}
        edges_raw = [
            e
            for e in edges_raw
            if str(e["source"]) in node_ids and str(e["target"]) in node_ids
        ]

    nodes, edges = _build_graph_elements(
        {"nodes": nodes_raw, "edges": edges_raw},
        search_query=search_query,
    )

    config = Config(
        width="100%",
        height=600,
        directed=True,
        hierarchical=True,
        physics=False,
    )

    clicked = agraph(nodes=nodes, edges=edges, config=config)

    if isinstance(clicked, str) and clicked != st.session_state.selected_node_id:
        st.session_state.selected_node_id = clicked


# основной рендер вкладки
def render_graph_tab():
    st.markdown(
        '<div class="main-header">Assembly Graph Visualization</div>',
        unsafe_allow_html=True,
    )

    if "graph_root" not in st.session_state:
        st.session_state.graph_root = None
    if "graph_data" not in st.session_state:
        st.session_state.graph_data = None
    if "selected_node_id" not in st.session_state:
        st.session_state.selected_node_id = None

    col_graph, col_side = st.columns([3, 1])

    with col_side:
        _, _ = _render_controls()
        search_query = _render_search_and_hybrid()
        _render_maintenance()

    with col_graph:
        _render_graph_area(search_query)

    _render_node_details()
