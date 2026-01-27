# pages/clustering_page.py
import streamlit as st


def render_clustering_tab():
    """Вкладка кластеризации"""
    st.markdown('<div class="main-header">Component Clustering and Analysis</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
        <h3 style="margin-top: 0; margin-bottom: 1rem;">Component Clustering</h3>
        <p style="color: #6B7280; margin-bottom: 1.5rem;">
            Perform clustering analysis on components based on their features and hierarchical relationships.
        </p>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-top: 1rem;">
            <div style="background-color: white; padding: 1.5rem; border-radius: 8px; border: 1px solid #E5E7EB;">
                <h4 style="margin-top: 0; margin-bottom: 1rem; font-size: 1rem;">Clustering Parameters</h4>
                <div style="margin-bottom: 1rem;">
                    <div class="control-label">Algorithm</div>
                    <select class="control-select">
                        <option>K-Means</option>
                        <option>DBSCAN</option>
                        <option>Hierarchical</option>
                        <option>HDBSCAN</option>
                    </select>
                </div>
                <div style="margin-bottom: 1rem;">
                    <div class="control-label">Number of Clusters</div>
                    <input type="range" min="2" max="20" value="5" style="width: 100%;">
                </div>
                <div style="margin-bottom: 1.5rem;">
                    <div class="control-label">Features</div>
                    <div style="margin-top: 0.5rem;">
                        <div style="display: flex; align-items: center; margin-bottom: 0.25rem;">
                            <input type="checkbox" checked style="margin-right: 0.5rem;">
                            <span>Description</span>
                        </div>
                        <div style="display: flex; align-items: center; margin-bottom: 0.25rem;">
                            <input type="checkbox" checked style="margin-right: 0.5rem;">
                            <span>Component Type</span>
                        </div>
                        <div style="display: flex; align-items: center; margin-bottom: 0.25rem;">
                            <input type="checkbox" style="margin-right: 0.5rem;">
                            <span>Material</span>
                        </div>
                        <div style="display: flex; align-items: center; margin-bottom: 0.25rem;">
                            <input type="checkbox" style="margin-right: 0.5rem;">
                            <span>Size Information</span>
                        </div>
                    </div>
                </div>
                <button style="width: 100%; padding: 0.75rem; background-color: #10B981; 
                              color: white; border: none; border-radius: 6px; cursor: pointer; 
                              font-weight: 500;">
                    Run Clustering Analysis
                </button>
            </div>

            <div style="background-color: white; padding: 1.5rem; border-radius: 8px; border: 1px solid #E5E7EB;">
                <h4 style="margin-top: 0; margin-bottom: 1rem; font-size: 1rem;">Cluster Visualization</h4>
                <div style="height: 250px; background-color: #F9FAFB; border-radius: 8px; 
                            display: flex; align-items: center; justify-content: center; 
                            border: 2px dashed #D1D5DB; margin-bottom: 1rem;">
                    <div style="text-align: center; color: #9CA3AF;">
                        <div style="font-size: 3rem; margin-bottom: 0.5rem;">📈</div>
                        <div>Cluster visualization will appear here</div>
                    </div>
                </div>
                <div style="font-size: 0.875rem; color: #6B7280;">
                    <strong>Note:</strong> Load and process data in the Data Upload tab first to enable clustering analysis.
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)# pages/clustering_page.py
import streamlit as st

def render_clustering_tab():
    """Вкладка кластеризации"""
    st.markdown('<div class="main-header">Component Clustering and Analysis</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
        <h3 style="margin-top: 0; margin-bottom: 1rem;">Component Clustering</h3>
        <p style="color: #6B7280; margin-bottom: 1.5rem;">
            Perform clustering analysis on components based on their features and hierarchical relationships.
        </p>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-top: 1rem;">
            <div style="background-color: white; padding: 1.5rem; border-radius: 8px; border: 1px solid #E5E7EB;">
                <h4 style="margin-top: 0; margin-bottom: 1rem; font-size: 1rem;">Clustering Parameters</h4>
                <div style="margin-bottom: 1rem;">
                    <div class="control-label">Algorithm</div>
                    <select class="control-select">
                        <option>K-Means</option>
                        <option>DBSCAN</option>
                        <option>Hierarchical</option>
                        <option>HDBSCAN</option>
                    </select>
                </div>
                <div style="margin-bottom: 1rem;">
                    <div class="control-label">Number of Clusters</div>
                    <input type="range" min="2" max="20" value="5" style="width: 100%;">
                </div>
                <div style="margin-bottom: 1.5rem;">
                    <div class="control-label">Features</div>
                    <div style="margin-top: 0.5rem;">
                        <div style="display: flex; align-items: center; margin-bottom: 0.25rem;">
                            <input type="checkbox" checked style="margin-right: 0.5rem;">
                            <span>Description</span>
                        </div>
                        <div style="display: flex; align-items: center; margin-bottom: 0.25rem;">
                            <input type="checkbox" checked style="margin-right: 0.5rem;">
                            <span>Component Type</span>
                        </div>
                        <div style="display: flex; align-items: center; margin-bottom: 0.25rem;">
                            <input type="checkbox" style="margin-right: 0.5rem;">
                            <span>Material</span>
                        </div>
                        <div style="display: flex; align-items: center; margin-bottom: 0.25rem;">
                            <input type="checkbox" style="margin-right: 0.5rem;">
                            <span>Size Information</span>
                        </div>
                    </div>
                </div>
                <button style="width: 100%; padding: 0.75rem; background-color: #10B981; 
                              color: white; border: none; border-radius: 6px; cursor: pointer; 
                              font-weight: 500;">
                    Run Clustering Analysis
                </button>
            </div>
            
            <div style="background-color: white; padding: 1.5rem; border-radius: 8px; border: 1px solid #E5E7EB;">
                <h4 style="margin-top: 0; margin-bottom: 1rem; font-size: 1rem;">Cluster Visualization</h4>
                <div style="height: 250px; background-color: #F9FAFB; border-radius: 8px; 
                            display: flex; align-items: center; justify-content: center; 
                            border: 2px dashed #D1D5DB; margin-bottom: 1rem;">
                    <div style="text-align: center; color: #9CA3AF;">
                        <div style="font-size: 3rem; margin-bottom: 0.5rem;">📈</div>
                        <div>Cluster visualization will appear here</div>
                    </div>
                </div>
                <div style="font-size: 0.875rem; color: #6B7280;">
                    <strong>Note:</strong> Load and process data in the Data Upload tab first to enable clustering analysis.
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)