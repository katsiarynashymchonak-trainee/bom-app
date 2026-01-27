# app.py
import streamlit as st
import sys
import os

from src.ui.pages.clustering_page import render_clustering_tab
from src.ui.pages.graph_page import render_graph_tab
from src.ui.pages.upload_page import render_upload_tab
from src.ui.styles import get_css_styles

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Настройка страницы
st.set_page_config(
    page_title="BOM Management System",
    layout="wide",
    initial_sidebar_state="expanded"
)

# SVG иконки
SVG_GRAPH = """
<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M1 1V17H19M3 13L7 9L10.5 12.5L17 6" stroke="#4B5563" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""

SVG_UPLOAD = """
<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M17 13V15C17 15.5304 16.7893 16.0391 16.4142 16.4142C16.0391 16.7893 15.5304 17 15 17H5C4.46957 17 3.96086 16.7893 3.58579 16.4142C3.21071 16.0391 3 15.5304 3 15V13M7 7L10 4M10 4L13 7M10 4V12" stroke="#4B5563" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""

SVG_CLUSTER = """
<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="7" cy="7" r="2" stroke="#4B5563" stroke-width="2"/>
    <circle cx="13" cy="7" r="2" stroke="#4B5563" stroke-width="2"/>
    <circle cx="10" cy="13" r="2" stroke="#4B5563" stroke-width="2"/>
    <path d="M7 9L10 12M10 12L13 9" stroke="#4B5563" stroke-width="2" stroke-linecap="round"/>
</svg>
"""

# Применяем CSS стили
st.markdown(get_css_styles(), unsafe_allow_html=True)


def main():
    """Главная функция приложения"""

    # Сайдбар
    with st.sidebar:
        st.markdown(f"""
        <div class="sidebar-section">
            <div class="sidebar-title">BOM Management System</div>
            <p style="color: #6B7280; font-size: 0.875rem; margin-bottom: 1.5rem;">
                Hierarchical Bill of Materials management for engineering assemblies.
            </p>
        </div>

        <div class="sidebar-section">
            <div class="sidebar-title">System Status</div>
            <div class="status-item">
                <div class="status-dot status-online"></div>
                <span>Application: Online</span>
            </div>
            <div class="status-item">
                <div class="status-dot status-online"></div>
                <span>Database: Connected</span>
            </div>
            <div class="status-item">
                <div class="status-dot status-warning"></div>
                <span>Processing: Ready</span>
            </div>
            <div class="status-item">
                <div class="status-dot status-online"></div>
                <span>Memory: Available</span>
            </div>
        </div>

        <div class="sidebar-section">
            <div class="sidebar-title">Quick Actions</div>
            <button class="quick-action">
                {SVG_GRAPH}
                <span>Generate Report</span>
            </button>
            <button class="quick-action">
                {SVG_UPLOAD}
                <span>Export Data</span>
            </button>
            <button class="quick-action">
                {SVG_CLUSTER}
                <span>System Settings</span>
            </button>
        </div>
        """, unsafe_allow_html=True)

    # Создаем вкладки
    tab1, tab2, tab3 = st.tabs([
        "Data Upload",
        "Assembly Graph",
        "Clustering"
    ])

    with tab1:
        render_upload_tab()

    with tab2:
        render_graph_tab()

    with tab3:
        render_clustering_tab()

    # Футер
    st.markdown("""
    <div style="margin-top: 3rem; padding-top: 1.5rem; border-top: 1px solid #E5E7EB;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div style="color: #6B7280; font-size: 0.875rem;">
                BOM Management System 
            </div>
            <div style="color: #6B7280; font-size: 0.875rem;">
                © 2026 Test task
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()