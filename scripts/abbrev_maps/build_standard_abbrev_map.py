import json
import requests

# Импорт путей и настроек для нормализации стандартов
from scripts.config import OLLAMA_URL, OLLAMA_MODEL, STANDARD_CLEAN, STANDARD_MAP


# Вызов LLM для нормализации инженерных стандартов
def call_llm(standards):
    prompt = f"""
You are normalizing engineering standard abbreviations.

Your task for EACH RAW standard token:
1. Identify whether the token represents a real engineering standard.
2. Normalize spacing:
   - ASME16.5 → ASME B16.5
   - API6A → API 6A
   - DIN2573 → DIN 2573
3. Normalize hyphens and slashes.
4. Map all variants to their base form:
   - ASTM A105 → ASTM
   - ASME B16.5 → ASME
   - ISO 5211 → ISO
   - UNC-2A → UNC
   - UNF-2B → UNF
   - SCH40 → SCH
   - RF03 → RF
   - FF03 → FF
5. Exclude:
   - materials
   - components
   - vendors
   - operations
   - parameters
   - noise codes

Return STRICT JSON ONLY:

{{
  "mapping": {{
      "RAW_TOKEN": "BASE_STANDARD"
  }}
}}

RAW_TOKENS:
{standards}
"""

    resp = requests.post(
        OLLAMA_URL,
        json={"model": OLLAMA_MODEL, "prompt": prompt},
        stream=True  # Потоковый вывод — LLM присылает ответ частями
    )

    buffer = ""
    for line in resp.iter_lines():
        if not line:
            continue
        try:
            obj = json.loads(line.decode())  # Каждая строка — JSON-объект с полем "response"
        except:
            continue
        if "response" in obj:
            buffer += obj["response"]  # Собираем текст ответа
        if obj.get("done"):
            break  # LLM сообщает, что вывод завершён

    # Поиск JSON внутри потока текста
    start = buffer.find("{")
    end = buffer.rfind("}")
    if start == -1 or end == -1:
        return {}  # Если JSON не найден — возвращаем пустой словарь

    data = json.loads(buffer[start:end+1].replace("'", '"'))  # Приводим к валидному JSON
    mapping = data.get("mapping", {}) or {}

    return {k.upper(): v.upper() for k, v in mapping.items()}  # Приводим ключи и значения к верхнему регистру


# Основная функция: загрузка стандартов, нормализация, сохранение результата
def main():
    with open(STANDARD_CLEAN, "r", encoding="utf-8") as f:
        import yaml
        data = yaml.safe_load(f) or {}  # Загружаем YAML, если пустой — {}
        standards = data.get("standards", [])  # Берём список стандартов

    mapping = call_llm(standards)  # Нормализуем через LLM

    with open(STANDARD_MAP, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)  # Сохраняем JSON-маппинг

    print(f"Saved standard abbreviation map to {STANDARD_MAP}")


if __name__ == "__main__":
    main()
