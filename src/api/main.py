# src/api/main.py

from fastapi import FastAPI
from src.db.init_db import init_db

# Роутеры API
from src.api.routes.components import router as components_router
from src.api.routes.search import router as search_router
from src.api.routes.cross_matching import router as cross_matching_router
from src.api.routes.stats import router as stats_router
from src.api.routes.imports import router as import_router
from src.api.routes.process import router as process_router
from src.api.routes.graph import router as graph_router
from src.api.routes.maintenance import router as maintenance_router
from src.api.routes.embeddings import router as embedding_router


import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

# Инициализация базы данных
init_db()

# Создание FastAPI приложения
app = FastAPI(
    title="BOM Intelligence API",
    description="Backend for hierarchical BOM management, vector search, analytics, and processing pipeline",
    version="2.0.0",
)

# Эндпоинт проверки состояния API
@app.get("/health")
def health_check():
    return {"status": "ok", "message": "API is running"}

# Регистрация роутеров
app.include_router(components_router)
app.include_router(search_router)
app.include_router(cross_matching_router)
app.include_router(stats_router)
app.include_router(import_router)
app.include_router(process_router)
app.include_router(graph_router)
app.include_router(maintenance_router)
app.include_router(embedding_router)
