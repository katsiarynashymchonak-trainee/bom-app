# pages/graph_page.py
import streamlit as st


def render_graph_tab():
    """Вкладка графа сборок"""
    st.markdown('<div class="main-header">Assembly Graph Visualization</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown("""
        <div class="card">
            <h3 style="margin-top: 0; margin-bottom: 1rem;">Hierarchical Graph View</h3>
            <p style="color: #6B7280; margin-bottom: 1rem;">Visual representation of assembly hierarchy and component relationships.</p>
            <div style="height: 400px; background-color: #F9FAFB; border-radius: 8px; 
                        display: flex; align-items: center; justify-content: center; 
                        border: 2px dashed #D1D5DB;">
                <div style="text-align: center;">
                    <div style="font-size: 3rem; color: #9CA3AF; margin-bottom: 1rem;">📊</div>
                    <div style="color: #6B7280; font-weight: 500;">Graph visualization</div>
                    <div style="color: #9CA3AF; font-size: 0.875rem; margin-top: 0.5rem;">
                        Load and process data in Data Upload tab first
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="card">
            <h3 style="margin-top: 0; margin-bottom: 1rem;">Graph Controls</h3>
            <div style="margin-bottom: 1rem;">
                <div class="control-label">Layout Type</div>
                <select class="control-select">
                    <option>Hierarchical</option>
                    <option>Force-Directed</option>
                    <option>Radial</option>
                    <option>Tree</option>
                </select>
            </div>
            <div style="margin-bottom: 1rem;">
                <div class="control-label">Depth Level</div>
                <input type="range" min="1" max="10" value="3" style="width: 100%;">
            </div>
            <div style="margin-bottom: 1.5rem;">
                <div class="control-label">Node Size</div>
                <select class="control-select">
                    <option>By Quantity</option>
                    <option>By Hierarchy Level</option>
                    <option>Uniform Size</option>
                </select>
            </div>
            <button style="width: 100%; padding: 0.75rem; background-color: #4F46E5; 
                          color: white; border: none; border-radius: 6px; cursor: pointer; 
                          font-weight: 500;">
                Refresh Graph
            </button>
        </div>
        """, unsafe_allow_html=True)