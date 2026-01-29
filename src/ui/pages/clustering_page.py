import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import umap
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from src.utils.api_client import api_get_embeddings


@st.cache_resource(show_spinner=False)
def load_embeddings_cached():
    data = api_get_embeddings()
    if not data:
        return None
    df = pd.DataFrame(data)
    df["vector"] = df["vector"].apply(np.array)
    return df


@st.cache_data(show_spinner=False)
def compute_umap(vectors: np.ndarray, dim: int):
    reducer = umap.UMAP(n_components=dim)
    return reducer, reducer.fit_transform(vectors)


@st.cache_data(show_spinner=False)
def compute_clustering(vectors: np.ndarray, algorithm: str, n_clusters: int):
    if algorithm == "K-Means":
        model = KMeans(n_clusters=n_clusters)
        labels = model.fit_predict(vectors)
        centroids = model.cluster_centers_
    elif algorithm == "DBSCAN":
        model = DBSCAN(eps=0.5, min_samples=5)
        labels = model.fit_predict(vectors)
        centroids = None
    else:
        model = AgglomerativeClustering(n_clusters=n_clusters)
        labels = model.fit_predict(vectors)
        centroids = None

    return labels, centroids



def render_clustering_tab():
    st.markdown('<div class="main-header">Component Clustering and Analysis</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
        <h3 style="margin-top: 0; margin-bottom: 1rem;">Component Clustering</h3>
        <p style="color: #6B7280; margin-bottom: 1.5rem;">
            Perform clustering analysis on components based on their embeddings and metadata.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 2])

    with col1:
        algorithm = st.selectbox("Algorithm", ["K-Means", "DBSCAN", "Hierarchical"])
        n_clusters = st.slider("Number of clusters (for K-Means)", 2, 20, 5)
        dim = st.radio("Visualization", ["2D", "3D"])
        run = st.button("Run clustering analysis", use_container_width=True)

    with col2:
        plot_placeholder = st.empty()

    if not run:
        return

    df = load_embeddings_cached()
    if df is None:
        st.error("No embeddings available. Load data first.")
        return

    vectors = np.vstack(df["vector"].values)

    labels, centroids = compute_clustering(vectors, algorithm, n_clusters)
    df["cluster"] = labels.astype(str)

    reducer, embedding = compute_umap(vectors, dim=3 if dim == "3D" else 2)

    if dim == "2D":
        df["x"] = embedding[:, 0]
        df["y"] = embedding[:, 1]

        fig = px.scatter(
            df,
            x="x",
            y="y",
            color="cluster",
            hover_name="id",
            title="Embedding Space Clusters (UMAP 2D)",
            opacity=0.85
        )

        # CENTROIDS
        if centroids is not None:
            centroids_2d = reducer.transform(centroids)
            fig.add_scatter(
                x=centroids_2d[:, 0],
                y=centroids_2d[:, 1],
                mode="markers",
                marker=dict(size=18, color="black", symbol="x"),
                name="Centroids"
            )

    else:
        df["x"] = embedding[:, 0]
        df["y"] = embedding[:, 1]
        df["z"] = embedding[:, 2]

        fig = px.scatter_3d(
            df,
            x="x",
            y="y",
            z="z",
            color="cluster",
            hover_name="id",
            title="Embedding Space Clusters (UMAP 3D)",
            opacity=0.85
        )

        if centroids is not None:
            centroids_3d = reducer.transform(centroids)
            fig.add_scatter3d(
                x=centroids_3d[:, 0],
                y=centroids_3d[:, 1],
                z=centroids_3d[:, 2],
                mode="markers",
                marker=dict(size=8, color="black", symbol="x"),
                name="Centroids"
            )

    plot_placeholder.plotly_chart(fig, use_container_width=True)
