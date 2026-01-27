# src/api/routes/imports.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.db.init_db import import_from_parquet

router = APIRouter(prefix="/import", tags=["import"])


class ImportResponse(BaseModel):
    imported_rows: int


@router.post("/parquet", response_model=ImportResponse)
def import_parquet():
    try:
        count = import_from_parquet()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="processed_bom.parquet not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

    return ImportResponse(imported_rows=count)
