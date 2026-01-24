import os
import json
import yaml
import requests

# Импорт путей и настроек для материалов
from scripts.config import (
    OLLAMA_MODEL,
    OLLAMA_URL,
    MATERIAL_CLEAN,
    MATERIAL_MAP
)


# Загрузка списка материалов из YAML с разворачиванием вложенных структур
def load_yaml_list(path, key):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
        raw = data.get(key, [])
    out = []

    def flatten(x):
        if isinstance(x, list):
            for i in x:
                flatten(i)
        elif isinstance(x, dict) or x is None:
            return
        else:
            out.append(str(x).strip().upper())

    flatten(raw)
    return out


# Вызов LLM для нормализации материалов
def call_llm(materials):
    prompt = f"""
You are normalizing engineering material abbreviations.

Your task for EACH RAW material token:
1. Expand abbreviations:
   - SS, SST, STST → STAINLESS STEEL
   - CS → CARBON STEEL
   - STL → STEEL
   - BRNZ, BRZ → BRONZE
   - ALUM → ALUMINUM
   - DI → DUCTILE IRON
   - CI → CAST IRON

2. Recognize steel grades:
   - 304, 304L, 316, 316L, 410, 4140, 4340, 1144, 1020, 403, 347, 450SS, etc.
   Normalize them to:
   - 304 STAINLESS STEEL
   - 316 STAINLESS STEEL
   - 4140 ALLOY STEEL
   - 1020 CARBON STEEL
   - 1144 CARBON STEEL

3. Recognize ASTM/API/SAE materials:
   - A105 → CARBON STEEL
   - A106 → CARBON STEEL
   - A182 F11 → ALLOY STEEL
   - A216 → CAST STEEL
   - A395 → DUCTILE IRON
   - WC6 → CAST STEEL
   - WCB → CAST STEEL
   - CA15 → CAST STAINLESS STEEL

4. Remove non-material words:
   - components (ROTOR, WHEEL, CASING, NOZZLE BLOCK)
   - vendors (FISHER, VOGT, LUFKIN)
   - operations (MACHINING, WELDMENT)
   - parameters (RPM, PSI, etc.)

5. Do NOT invent new materials.
6. If a token cannot be normalized to a known material, skip it.

Return STRICT JSON ONLY:

{{
  "mapping": {{
      "RAW_TOKEN": "NORMALIZED_MATERIAL"
  }}
}}

RAW_TOKENS:
{materials}
"""

    resp = requests.post(
        OLLAMA_URL,
        json={"model": OLLAMA_MODEL, "prompt": prompt},
        stream=True
    )

    buffer = ""
    for line in resp.iter_lines():
        if not line:
            continue
        try:
            obj = json.loads(line.decode())
        except:
            continue
        if "response" in obj:
            buffer += obj["response"]
        if obj.get("done"):
            break

    start = buffer.find("{")
    end = buffer.rfind("}")
    if start == -1 or end == -1:
        return {}

    data = json.loads(buffer[start:end+1].replace("'", '"'))
    mapping = data.get("mapping", {}) or {}

    return {k.upper(): v.upper() for k, v in mapping.items()}


# Загрузка материалов, нормализация, сохранение маппинга
def main():
    materials = load_yaml_list(MATERIAL_CLEAN, "materials")
    mapping = call_llm(materials)

    with open(MATERIAL_MAP, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)

    print("Saved:", MATERIAL_MAP)


if __name__ == "__main__":
    main()
