import streamlit as st
import pandas as pd
import requests

from src.utils.logger import log
from src.utils.api_client import (
    api_get_components,
    api_get_stats,
    api_delete_component,
    api_search_components,
)
from src.utils.table_manager import DataTableManager

API_URL = "http://localhost:8000"

# кэширование статистики
@st.cache_data
def _load_stats():
    return api_get_stats()

# кэширование примера данных
@st.cache_data
def _load_components_sample():
    return api_get_components(limit=50, offset=0)


# диалог редактирования компонента
@st.dialog("Edit Component")
def edit_component_dialog():
    row = st.session_state.get("edit_row")
    if not row:
        st.write("No row selected")
        if st.button("Close"):
            st.session_state["edit_row"] = None
            st.rerun()
        return

    st.write(f"Editing component ID {row['id']}")

    updated = {}
    for col, val in row.items():
        if col in ["id", "unique_id", "Select"]:
            continue
        updated[col] = st.text_input(col, value=str(val))

    col1, col2 = st.columns(2)

    if col1.button("Save"):
        payload = {k: v for k, v in updated.items()}
        r = requests.patch(f"{API_URL}/components/{row['id']}", json=payload)

        if r.status_code == 200:
            st.success("Updated successfully")

            # сброс кэша таблицы
            st.session_state.components_cache = {}

            manager: DataTableManager = st.session_state.table_manager
            offset = (manager.current_page - 1) * manager.page_size
            components = api_get_components(limit=manager.page_size, offset=offset)
            table_df = pd.DataFrame(components)
            manager.set_data(table_df)

            st.session_state["edit_row"] = None
            st.rerun()
        else:
            st.error("Update failed")

    if col2.button("Cancel"):
        st.session_state["edit_row"] = None
        st.rerun()


# основная вкладка загрузки и обработки данных
def render_upload_tab():
    st.markdown('<div class="main-header">Data Upload and Processing</div>', unsafe_allow_html=True)

    if "logs" not in st.session_state:
        st.session_state.logs = []

    # инициализация кэша таблицы
    if "components_cache" not in st.session_state:
        st.session_state.components_cache = {}

    # состояние базы данных
    st.markdown('<div class="section-header">Current Database State</div>', unsafe_allow_html=True)

    try:
        stats = _load_stats()
        total_records = stats.get("total", 0)
        components_sample = _load_components_sample()
        df_sample = pd.DataFrame(components_sample)
    except Exception as e:
        df_sample = pd.DataFrame()
        stats = {}
        total_records = 0
        st.error("Unable to fetch database state.")
        log(f"Failed to fetch DB state: {e}")

    if total_records == 0:
        st.info("Database is empty. Upload a CSV file to begin.")
    else:
        st.success(f"Database contains {total_records:,} records")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Records", stats.get("total", 0))
        col2.metric("Assemblies", stats.get("assemblies", 0))
        col3.metric("Subassemblies", stats.get("subassemblies", 0))
        col4.metric("Leaf Components", stats.get("leafs", 0))

        st.markdown("### Sample of existing data")
        st.dataframe(df_sample.head(10), use_container_width=True)

    # загрузка CSV
    st.markdown('<div class="section-header">Step 1: Upload CSV</div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Select BOM CSV file",
        type=["csv"],
        help="Required columns: material_id, component_id, description, qty, path",
    )

    if uploaded_file:
        try:
            df_preview = pd.read_csv(uploaded_file, nrows=10)
            st.write("Preview (first 10 rows):")
            st.dataframe(df_preview, use_container_width=True)
        except Exception:
            st.warning("Could not preview file.")

        if st.button("Run Processing Pipeline", type="primary"):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue())}

            try:
                r = requests.post(f"{API_URL}/process/start", files=files, timeout=60)
                r.raise_for_status()
                task_id = r.json().get("task_id")
                st.session_state["processing_task_id"] = task_id
                st.info("Processing pipeline started.")
            except Exception as e:
                st.error("Failed to start processing pipeline.")
                log(f"Failed to start pipeline: {e}")
                return

    # статус обработки
    task_id = st.session_state.get("processing_task_id")
    if task_id:
        st.markdown('<div class="section-header">Step 2: Processing Status</div>', unsafe_allow_html=True)

        try:
            status = requests.get(f"{API_URL}/process/status/{task_id}", timeout=10).json()
        except Exception as e:
            status = {"status": "error", "message": "Failed to fetch status", "error": str(e)}

        state = status.get("status")

        if state not in ["done", "error"]:
            st.info("Processing pipeline is running…")
            return

        st.session_state["processing_task_id"] = None

        if state == "done":
            st.success("Processing completed successfully")

            st.info("Rebuilding graph cache…")

            try:
                r = requests.post(f"{API_URL}/maintenance/rebuild_graph", timeout=120)
                r.raise_for_status()
                st.success("Graph cache rebuilt successfully.")
            except Exception as e:
                st.error("Failed to rebuild graph cache.")
                log(f"Graph rebuild failed: {e}")
                return

            # сброс кэша таблицы
            st.session_state.components_cache = {}

            st.rerun()

        else:
            st.error("Processing pipeline failed.")
            st.rerun()

    # таблица базы данных
    st.markdown('<div class="section-header">Database Table</div>', unsafe_allow_html=True)

    if "table_manager" not in st.session_state:
        components_page = api_get_components(limit=50, offset=0)
        table_df = pd.DataFrame(components_page)
        st.session_state.table_manager = DataTableManager(table_df)
        st.session_state.table_manager.page_size = 50
    else:
        manager: DataTableManager = st.session_state.table_manager
        offset = (manager.current_page - 1) * manager.page_size

        cache_key = f"{offset}_{manager.page_size}"

        if cache_key not in st.session_state.components_cache:
            components_page = api_get_components(limit=manager.page_size, offset=offset)
            st.session_state.components_cache[cache_key] = pd.DataFrame(components_page)

        table_df = st.session_state.components_cache[cache_key]
        manager.set_data(table_df)

    manager: DataTableManager = st.session_state.table_manager

    # поиск
    search_col1, search_col2 = st.columns([3, 1])

    with search_col1:
        search_query = st.text_input(
            "Search",
            value=st.session_state.get("search_query", ""),
            key="search_query_input"
        )

    with search_col2:
        search_column = st.selectbox(
            "Column",
            manager.get_searchable_columns(),
            index=0,
            key="search_column_select"
        )

    st.session_state.search_query = search_query
    st.session_state.search_column = search_column

    if search_query.strip():
        results = api_search_components(
            query=search_query,
            column=search_column if search_column != "all" else None,
            limit=500
        )
        table_df = pd.DataFrame(results)
        manager.set_data(table_df)
    else:
        offset = (manager.current_page - 1) * manager.page_size
        cache_key = f"{offset}_{manager.page_size}"

        if cache_key not in st.session_state.components_cache:
            components_page = api_get_components(limit=manager.page_size, offset=offset)
            st.session_state.components_cache[cache_key] = pd.DataFrame(components_page)

        table_df = st.session_state.components_cache[cache_key]
        manager.set_data(table_df)

    page_data, _, total_items_local = manager.get_paged_data()

    real_total = stats.get("total", total_items_local)
    real_total_pages = max(1, (real_total + manager.page_size - 1) // manager.page_size)

    st.write(f"Total records in DB: {real_total}")
    st.write(f"Page {manager.current_page} of {real_total_pages}")

    if not page_data.empty:
        editable_df = page_data.copy()
        editable_df["Select"] = False

        edited_df = st.data_editor(
            editable_df,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "Select": st.column_config.CheckboxColumn("✔", help="Select row"),
            },
            key="editable_table",
        )

        selected_rows = edited_df[edited_df["Select"] == True]

        col_edit, col_delete = st.columns(2)

        if col_edit.button("✏️ Edit selected"):
            if not selected_rows.empty:
                st.session_state["edit_row"] = selected_rows.iloc[0].to_dict()
                edit_component_dialog()
            else:
                st.warning("No row selected")

        if col_delete.button("🗑️ Delete selected"):
            if selected_rows.empty:
                st.warning("No rows selected")
            else:
                for _, row in selected_rows.iterrows():
                    component_id = int(row["id"])
                    ok = api_delete_component(component_id)
                    if ok:
                        st.success(f"Deleted component {component_id}")
                    else:
                        st.error(f"Failed to delete component {component_id}")

                # сброс кэша таблицы
                st.session_state.components_cache = {}

                offset = (manager.current_page - 1) * manager.page_size
                components_page = api_get_components(limit=manager.page_size, offset=offset)
                table_df = pd.DataFrame(components_page)
                manager.set_data(table_df)
                st.rerun()

    col_prev, col_next = st.columns(2)

    if col_prev.button("Previous"):
        if manager.current_page > 1:
            manager.prev_page()
            st.rerun()

    if col_next.button("Next"):
        max_page = max(1, (real_total + manager.page_size - 1) // manager.page_size)
        if manager.current_page < max_page:
            manager.next_page()
            st.rerun()

    with st.expander("Logs"):
        for entry in st.session_state.logs:
            st.text(entry)
