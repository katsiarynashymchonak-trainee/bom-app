# src/db/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

from scripts.config import ROOT_DIR

DB_PATH = os.path.join(ROOT_DIR, "data", "bom.sqlite3")
DB_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DB_URL,
    echo=False,
    future=True,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True,
)

Base = declarative_base()
