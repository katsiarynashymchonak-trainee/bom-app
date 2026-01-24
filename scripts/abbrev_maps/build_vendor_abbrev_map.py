import os
import json
import yaml
import requests

# Импорт настроек и путей для нормализации вендоров
from scripts.config import (
    OLLAMA_MODEL,
    OLLAMA_URL,
    VENDOR_CLEAN,
    VENDOR_MAP
)


# Загрузка списка вендоров из YAML с разворачиванием вложенных структур
def load_yaml_list(path, key):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
        raw = data.get(key, [])
    out = []

    def flatten(x):
        # Рекурсивное разворачивание вложенных списков
        if isinstance(x, list):
            for i in x:
                flatten(i)
        elif isinstance(x, dict) or x is None:
            return
        else:
            out.append(str(x).strip().upper())  # Приведение к строке и верхнему регистру

    flatten(raw)
    return out


# Вызов LLM для нормализации вендоров
def call_llm(vendors):
    prompt = f"""
You are normalizing engineering vendor/manufacturer abbreviations.

Your task for EACH RAW vendor token:
1. Identify whether the token represents a real vendor/manufacturer brand.
   A vendor is typically:
   - a company that manufactures equipment
   - a company that manufactures components
   - a company that manufactures materials or coatings
   - a company that manufactures sensors, electronics, pumps, valves, actuators, seals, etc.

2. Exclude tokens that are NOT vendors:
   - materials (e.g., STAINLESS STEEL, WCB, MONEL, BRONZE, 316 SST, 4140)
   - component types (e.g., SHAFT, TRIP, GUSSETS, TACHOMETER)
   - standards (e.g., API, ASME, ASTM, ISO)
   - operations (e.g., MACHINING, REBUILD, WELDMENT)
   - parameters (e.g., RPM, PSI, FT-LB)
   - geographic names (e.g., ALBERTA, NEVADA)
   - noise codes (e.g., 00T6112, A48 CL30)

3. You can short vendor names:
   - ASCO SOLENOID → ASCO
   - LUFKIN GEAR → LUFKIN
   - HUB CITY GEAR → HUB CITY
   - XYLAN 1014 → XYLAN
   - MONEL 400 → MONEL (only if MONEL is used as a brand)
   - Remove trailing model numbers, sizes, or parameters.

4. Do NOT invent new vendors.
5. If a token cannot be confidently recognized as a vendor, skip it.

Return STRICT JSON ONLY:

{{
  "mapping": {{
      "RAW_TOKEN": "NORMALIZED_VENDOR"
  }}
}}

RAW_TOKENS:
{vendors}
"""

    resp = requests.post(
        OLLAMA_URL,
        json={"model": OLLAMA_MODEL, "prompt": prompt},
        stream=True  # Потоковый вывод от модели
    )

    buffer = ""
    for line in resp.iter_lines():
        if not line:
            continue
        try:
            obj = json.loads(line.decode())  # Каждая строка содержит JSON с полем response
        except:
            continue
        if "response" in obj:
            buffer += obj["response"]  # Накопление текста ответа
        if obj.get("done"):
            break  # Модель завершила вывод

    # Поиск JSON внутри потока текста
    start = buffer.find("{")
    end = buffer.rfind("}")
    if start == -1 or end == -1:
        return {}  # Если JSON не найден, возвращаем пустой словарь

    data = json.loads(buffer[start:end+1].replace("'", '"'))  # Приведение к валидному JSON
    mapping = data.get("mapping", {}) or {}

    return {k.upper(): v.upper() for k, v in mapping.items()}  # Приведение ключей и значений к верхнему регистру


# Основная функция загрузки вендоров и сохранения нормализованного маппинга
def main():
    vendors = load_yaml_list(VENDOR_CLEAN, "vendors")  # Загрузка очищенного списка вендоров

    mapping = call_llm(vendors)  # Нормализация через LLM

    with open(VENDOR_MAP, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)  # Сохранение результата

    print("Saved:", VENDOR_MAP)


if __name__ == "__main__":
    main()
