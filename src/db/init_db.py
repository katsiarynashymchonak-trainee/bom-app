import os
from typing import Optional

import pandas as pd
from sqlalchemy import text

from scripts.config import ROOT_DIR
from src.db.database import Base, engine, SessionLocal
from src.core.component_service import ComponentService
from src.core.models import ComponentCreate
from src.db.models import ComponentDB


# Инициализация структуры базы данных
def init_db() -> None:
    os.makedirs(os.path.join(ROOT_DIR, "data"), exist_ok=True)
    Base.metadata.create_all(bind=engine)


# Импорт данных из parquet файла в SQLite через сервисный слой
def import_from_parquet(parquet_path: Optional[str] = None) -> int:

    if parquet_path is None:
        parquet_path = os.path.join(
            ROOT_DIR, "data", "processed", "processed_bom.parquet"
        )

    if not os.path.exists(parquet_path):
        raise FileNotFoundError(f"Parquet file not found: {parquet_path}")

    df = pd.read_parquet(parquet_path)

    valid_columns = set(ComponentDB.__table__.columns.keys())
    df = df[[c for c in df.columns if c in valid_columns]]

    init_db()
    engine.dispose()

    with SessionLocal() as session:
        session.execute(text("DELETE FROM components"))
        session.commit()

        rows = df.to_dict(orient="records")
        objects = [ComponentDB(**row) for row in rows]

        session.bulk_save_objects(objects)
        session.commit()

        return len(objects)

