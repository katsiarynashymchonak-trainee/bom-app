import os
import yaml
import pandas as pd
import requests
import json
import logging
import subprocess
import re

# Импорт путей и настроек проекта
from scripts.config import (
    OLLAMA_URL,
    OLLAMA_MODEL,
    DESCRIPTIONS_PATH,
    GENERATE_DICT, CREATE_ABBREV_MAPS, NORM_DICTS, MATERIAL_RAW, SIZES_RAW, STANDARD_RAW, VENDOR_RAW, COMPONENT_RAW
)

# Базовые директории скрипта
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

# Пути к скриптам генерации маппингов и нормализации
ABBREV_DIR = os.path.join(ROOT_DIR, "scripts", "abbrev_maps")
NORM_DIR = os.path.join(ROOT_DIR, "scripts", "normalization")

# Размер чанка для обработки описаний
CHUNK_SIZE = 200

# Настройки логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    encoding="utf-8"
)


# Функция для запуска дочерних скриптов с выводом stdout/stderr
def run_script(path):
    print(f"\n=== Running {path} ===\n")
    result = subprocess.run(
        ["python", path],
        text=True,
        capture_output=True
    )
    print(result.stdout)
    print(result.stderr)
    if result.returncode != 0:
        print(f"ERROR in {path}: {result.returncode}")
    print(f"=== Finished {path} ===\n")


# Блок нормализации ключей результата
def normalize_result_keys(data):
    target = {
        "materials": [],
        "sizes": [],
        "standards": [],
        "vendors": [],
        "component_types": []
    }

    if not isinstance(data, dict):
        return target

    aliases = {
        "materials": ["material", "mats", "mat"],
        "sizes": ["size", "dimension", "dimensions", "dims"],
        "standards": ["standard", "std", "spec", "specs"],
        "vendors": ["vendor", "maker", "manufacturers"],
        "component_types": ["types", "type", "components", "component", "comp_types"]
    }

    for canonical, keys in aliases.items():
        if canonical in data and isinstance(data[canonical], list):
            target[canonical] = data[canonical]
            continue

        for alias in keys:
            if alias in data and isinstance(data[alias], list):
                target[canonical] = data[alias]
                break

    return target


# Блок извлечения JSON из произвольного текста
def extract_json(text):
    candidates = re.findall(r"\{[\s\S]*?\}", text)
    if not candidates:
        return None

    candidates = sorted(candidates, key=len, reverse=True)

    for block in candidates:
        cleaned = block.strip()

        try:
            return json.loads(cleaned)
        except:
            pass

        try:
            fixed = cleaned.replace("'", '"')
            return json.loads(fixed)
        except:
            pass

        try:
            fixed = re.sub(r",\s*([}\]])", r"\1", cleaned)
            return json.loads(fixed)
        except:
            pass

        try:
            fixed = re.sub(r"(\w+):", r'"\1":', cleaned)
            return json.loads(fixed)
        except:
            pass

        try:
            fixed = re.sub(r",\s*,", ",", cleaned)
            return json.loads(fixed)
        except:
            pass

    return None


# Блок восстановления JSON через LLM
def repair_json_with_llm(text):
    prompt = f"""
You will be given model output that is NOT valid JSON.

Your task is to convert it into STRICT VALID JSON that matches this schema:

{{
  "materials": [],
  "sizes": [],
  "standards": [],
  "vendors": [],
  "component_types": []
}}

Rules:
1. Output STRICT JSON only.
2. No explanations, no comments, no markdown.
3. If a field is missing, include it as an empty list.
4. If you cannot extract something, leave the list empty.
5. Never invent new values.

Convert the following text into valid JSON:

{text}
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
        return None

    try:
        return json.loads(buffer[start:end+1])
    except:
        return None


# Блок вызова LLM для извлечения сущностей
def call_llm(chunk_text):
    prompt = f"""
You analyze technical component descriptions.
You must extract dictionaries for the categories: materials, sizes, standards, vendors, component_types.

Important rules:
- Do NOT invent entities.
- Extract only what actually appears in the text.
- Return STRICT JSON only.

Component type examples:
ACTUATOR, ADAPTER, ANGLE, ASSEMBLY, BEARING, BLADE, BOLT, BOLTING, BRACKET,
BUSHING, BUSH, CAPSCREW, CASE, CASING, COLLAR, CONNECTOR, COUPLING, COVER,
CYLINDER, DRAIN, ELBOW, FITTING, FLANGE, GASKET, GAUGE, GAUGEBOARD, GOVERNOR,
HANDLE, HARDWARE, HOUSING, INLET, KEY, LABYRINTH, LEAKOFF, LEVER, LINKAGE....

Return STRICT JSON:
{{
  "materials": [],
  "sizes": [],
  "standards": [],
  "vendors": [],
  "component_types": []
}}

Text:
{chunk_text}
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

    logging.info("LLM raw output:\n%s", buffer)

    data = extract_json(buffer)
    if isinstance(data, dict):
        return normalize_result_keys(data)

    repaired = repair_json_with_llm(buffer)
    if isinstance(repaired, dict):
        return normalize_result_keys(repaired)

    logging.warning("Failed to extract JSON even after repair")
    return {
        "materials": [],
        "sizes": [],
        "standards": [],
        "vendors": [],
        "component_types": []
    }


# Вспомогательные функции для YAML
def load_yaml_set(path, key):
    if not os.path.exists(path):
        return set()
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
        raw = data.get(key, [])
    flat = set()

    def flatten(x):
        if isinstance(x, list):
            for item in x:
                flatten(item)
        elif isinstance(x, dict) or x is None:
            return
        else:
            flat.add(str(x))

    flatten(raw)
    return flat


def save_yaml(path, key, values):
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump({key: sorted(values)}, f, allow_unicode=True, default_style=None)


# Блок основного пайплайна
def main():


    materials = load_yaml_set(MATERIAL_RAW, "materials")
    sizes = load_yaml_set(SIZES_RAW, "sizes")
    standards = load_yaml_set(STANDARD_RAW, "standards")
    vendors = load_yaml_set(VENDOR_RAW, "vendors")
    component_types = load_yaml_set(COMPONENT_RAW, "component_types")

    if GENERATE_DICT:
        logging.info("=== Dictionary generation started ===")
        print("=== Dictionary generation started ===")

        df = pd.read_csv(DESCRIPTIONS_PATH, dtype=str)
        descriptions = df.iloc[:, 1].dropna().astype(str).tolist()
        total = len(descriptions)

        for i in range(0, total, CHUNK_SIZE):
            chunk = descriptions[i:i + CHUNK_SIZE]
            logging.info("Processing chunk %s–%s", i, i + len(chunk))
            print(f"\n=== Processing chunk {i}–{i + len(chunk)} of {total} ===\n")

            result = call_llm("\n".join(chunk))

            materials |= set(result["materials"])
            sizes |= set(result["sizes"])
            standards |= set(result["standards"])
            vendors |= set(result["vendors"])
            component_types |= set(result["component_types"])

            save_yaml(MATERIAL_RAW, "materials", materials)
            save_yaml(SIZES_RAW, "sizes", sizes)
            save_yaml(STANDARD_RAW, "standards", standards)
            save_yaml(VENDOR_RAW, "vendors", vendors)
            save_yaml(COMPONENT_RAW, "component_types", component_types)

        logging.info("Dictionary generation complete")
        print("Dictionary generation complete")

    if CREATE_ABBREV_MAPS:
        # Запуск всех build_* с выводом stdout/stderr
        run_script(os.path.join(ABBREV_DIR, "build_vendor_abbrev_map.py"))
        run_script(os.path.join(ABBREV_DIR, "build_standard_abbrev_map.py"))
        run_script(os.path.join(ABBREV_DIR, "build_component_abbrev_map.py"))
        run_script(os.path.join(ABBREV_DIR, "build_material_abbrev_map.py"))

    if NORM_DICTS:
        # Запуск нормализации
        run_script(os.path.join(NORM_DIR, "normalize_vendors.py"))
        run_script(os.path.join(NORM_DIR, "normalize_standards.py"))
        run_script(os.path.join(NORM_DIR, "normalize_component_types.py"))
        run_script(os.path.join(NORM_DIR, "normalize_materials.py"))

        logging.info("All dictionaries normalized")
        print("All dictionaries normalized")


if __name__ == "__main__":
    main()
