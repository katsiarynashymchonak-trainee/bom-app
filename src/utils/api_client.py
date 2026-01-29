import requests
from src.utils.logger import log

API_URL = "http://localhost:8000"


def api_call(method: str, url: str, **kwargs):
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
    r = api_call(
        "get",
        "/components",
        params={"limit": limit, "offset": offset}
    )

    if r and r.status_code == 200:
        return r.json()

    return []


def api_get_stats():
    r = api_call("get", "/stats")
    if r and r.status_code == 200:
        return r.json()
    return {}


def api_import_parquet():
    r = api_call("post", "/import/parquet")
    if r and r.status_code == 200:
        return r.json()
    return {"imported_rows": 0}


def api_delete_component(component_id: int):
    r = api_call("delete", f"/components/{component_id}")
    return r and r.status_code == 200


def api_get_graph(max_depth=3, root_id=None):
    params = {"max_depth": max_depth}
    if root_id:
        params["root_id"] = root_id
    r = requests.get(f"{API_URL}/graph", params=params)
    r.raise_for_status()
    return r.json()


def api_get_material_ids():
    r = requests.get(f"{API_URL}/components/material_ids")
    r.raise_for_status()
    return r.json()

def api_get_vendors():
    r = requests.get(f"{API_URL}/components/vendors")
    r.raise_for_status()
    return r.json()


def api_search_components(query: str, column: str = None, record_types=None, limit: int = 20):
    payload = {
        "query": query,
        "limit": limit,
    }
    if column:
        payload["column"] = column
    if record_types:
        payload["record_types"] = record_types

    r = requests.post(f"{API_URL}/search/components", json=payload)
    r.raise_for_status()
    return r.json()


def api_get_component(component_id: str | int):
    r = requests.get(f"{API_URL}/components/{component_id}")
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()


def api_get_similar_components(component_id: int, limit: int = 10, same_level_only=False):
    url = f"{API_URL}/cross-matching/{component_id}?top_k={limit}&same_level_only={str(same_level_only).lower()}"
    r = requests.get(url)
    r.raise_for_status()
    return r.json()


def api_hybrid_search(
    query: str,
    record_types=None,
    material_id: str | None = None,
    vendor: str | None = None,
    top_k: int = 20,
):
    payload = {
        "query": query,
        "top_k": top_k,
    }

    if record_types:
        payload["record_types"] = record_types

    if material_id:
        payload["material_id"] = material_id

    if vendor:
        payload["vendor"] = vendor

    r = requests.post(f"{API_URL}/search/hybrid", json=payload)
    r.raise_for_status()
    return r.json()


