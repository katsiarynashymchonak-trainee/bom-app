from fastapi import APIRouter, UploadFile, File
import shutil
import os

from scripts.config import RAW_DATA_DIR
from src.core.process_service import start_processing
from src.core.task_manager import TaskManager

router = APIRouter(prefix="/process", tags=["processing"])


@router.post("/start")
def start_process(file: UploadFile = File(...)):
    os.makedirs(RAW_DATA_DIR, exist_ok=True)

    raw_path = os.path.join(RAW_DATA_DIR, file.filename)
    with open(raw_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    task_id = start_processing(raw_path)
    return {"task_id": task_id}


@router.get("/status/{task_id}")
def get_status(task_id: str):
    task = TaskManager.get(task_id)
    if not task:
        return {"error": "Task not found"}
    return task
