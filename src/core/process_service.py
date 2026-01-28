# src/core/process_service.py

import uuid
import logging
import os
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

from src.pipeline.processor import SimpleBOMProcessor
from src.core.task_manager import TaskManager
from src.db.init_db import import_from_parquet

logger = logging.getLogger(__name__)

# глобальный пул потоков
executor = ThreadPoolExecutor(max_workers=4)


# запуск фоновой обработки
def start_processing(file_path: str) -> str:
    task_id = str(uuid.uuid4())
    TaskManager.create(task_id)

    logger.info("Submitting background task %s for file %s", task_id, file_path)

    executor.submit(run_processing, task_id, file_path)

    return task_id


# фоновая задача обработки CSV и импорта в БД
def run_processing(task_id: str, file_path: str) -> None:
    logger.info("run_processing STARTED for task %s, file %s", task_id, file_path)

    try:
        # чтение CSV
        TaskManager.update(task_id, status="running", progress=5, message="Reading CSV file...")
        df = pd.read_csv(file_path)

        # запуск пайплайна
        TaskManager.update(task_id, progress=20, message="Running processing pipeline...")
        processor = SimpleBOMProcessor()
        processed_df = processor.process_pipeline(df)
        stats = processor.get_stats()

        logger.info("Task %s: processed %d rows", task_id, len(processed_df))

        # сохранение parquet
        TaskManager.update(task_id, progress=60, message="Saving processed parquet...")

        output_dir = "data/processed"
        output_path = os.path.join(output_dir, "processed_bom.parquet")

        os.makedirs(output_dir, exist_ok=True)
        processed_df.to_parquet(output_path, index=False)

        logger.info("Task %s: parquet saved to %s", task_id, output_path)

        # импорт parquet в БД
        TaskManager.update(task_id, progress=80, message="Importing into database...")
        imported_rows = import_from_parquet()

        summary_msg = (
            f"Processing completed successfully "
            f"({imported_rows} rows imported; "
        )

        # завершение
        TaskManager.update(
            task_id,
            status="done",
            progress=100,
            message=summary_msg,
        )

        logger.info("Task %s completed successfully — %s", task_id, summary_msg)

    except Exception as e:
        logger.exception("Task %s failed: %s", task_id, str(e))
        TaskManager.update(
            task_id,
            status="error",
            progress=100,
            message="Processing failed.",
            error=str(e),
        )
