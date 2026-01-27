import requests
from src.utils.logger import log

API_URL = "http://localhost:8000"


def api_call(method: str, url: str, **kwargs):
    """Единая обёртка для всех API запросов с логированием ошибок."""
    try:
        response = requests.request(
            method,
            f"{API_URL}{url}",
            timeout=20,
            **kwargs
        )

        if response.status_code >= 400:
            try:
                detail = response.json().get("detail")
                log(f"API error: {detail}")
            except Exception:
                log(f"API error: {response.text}")

        return response

    except Exception as e:
        log(f"API connection error: {str(e)}")
        return None


def api_get_components(limit: int = 50, offset: int = 0):
    """
    Получение списка компонентов с серверной пагинацией.
    limit — сколько строк получить
    offset — смещение
    """
    r = api_call(
        "get",
        "/components",
        params={"limit": limit, "offset": offset}
    )

    if r and r.status_code == 200:
        return r.json()

    return []


def api_get_stats():
    """Получение статистики по базе данных."""
    r = api_call("get", "/stats")
    if r and r.status_code == 200:
        return r.json()
    return {}


def api_import_parquet():
    """Импорт parquet файла (если используется)."""
    r = api_call("post", "/import/parquet")
    if r and r.status_code == 200:
        return r.json()
    return {"imported_rows": 0}


def api_delete_component(component_id: int):
    """Удаление компонента по ID."""
    r = api_call("delete", f"/components/{component_id}")
    return r and r.status_code == 200
