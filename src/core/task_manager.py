import threading
from typing import Dict, Optional


# Менеджер фоновых задач с потокобезопасным доступом
class TaskManager:
    _lock = threading.Lock()
    _tasks: Dict[str, Dict] = {}

    # Создание новой задачи
    @classmethod
    def create(cls, task_id: str) -> None:
        with cls._lock:
            cls._tasks[task_id] = {
                "status": "created",
                "progress": 0,
                "message": "Task created",
                "error": None,
            }

    # Обновление состояния задачи
    @classmethod
    def update(cls, task_id: str, **kwargs) -> None:
        with cls._lock:
            if task_id in cls._tasks:
                cls._tasks[task_id].update(kwargs)

    # Получение состояния задачи
    @classmethod
    def get(cls, task_id: str) -> Optional[Dict]:
        with cls._lock:
            return cls._tasks.get(task_id)
