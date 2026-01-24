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
    DICT_DIR,
    OLLAMA_URL,
    OLLAMA_MODEL,
    DESCRIPTIONS_PATH,
    GENERATE_DICT
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
HANDLE, HARDWARE, HOUSING, INLET, KEY, LABYRINTH, LEAKOFF, LEVER, LINKAGE,
LOCKNUT, LOCKWASHER, LUBRICATION, MOUNTING, NAMEPLATE, NIPPLE, NOZZLE, NUT,
ORIFICE, PACKING, PIPE, PIPEGUARD, PIPEPLUG, PIPING, PUMP, REDUCER, RING,
ROLLPIN, ROTATION, ROTOR, SCREW, SEAL, SEALANT, SECTOR, SETSCREW, SHAFT,
SHROUDBAND, SHSS, SIPHON, SOLENOID, SOLEPLATE, SPACER, SPRING, STEM, STUD,
TACHOMETER, TAPPET, TEE, THERMOMETER, THROTTLE, TRIP, TRUNNION, TURBINE, TURB,
UNION, VALVE, WASHER, WHEEL, BODY, BONNET, GEAR, BOX, BUCKET, BUMPER, CAGE,
BORD, CIRC, CLAPPER, CONDENSER, EJECTOR, TRANSFORMER, CONTROLLER, ENCLOSURE,
EYEBOLT, STUB, COOLER, LUBE, PINION, SPUR, GLAND, PIN, INDICATOR, IMPELLER,
BLANKET, SWITCH, PURGE, PRESS, PORT, SOFTWARE, TRANSDUCER, SENSOR, PROBE,
STK, SCREEN, SEAT, SET, SIGNAL, SILENCER, VENT, SLEEVE, THRUST, TUBE,
VELOMITOR, TRANSMITTER, WARNING, WATER COOL.

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
        return data

    repaired = repair_json_with_llm(buffer)
    if isinstance(repaired, dict):
        return repaired

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
    logging.info("=== Dictionary generation started ===")
    print("=== Dictionary generation started ===")

    materials = load_yaml_set(os.path.join(DICT_DIR, "materials.yaml"), "materials")
    sizes = load_yaml_set(os.path.join(DICT_DIR, "sizes.yaml"), "sizes")
    standards = load_yaml_set(os.path.join(DICT_DIR, "standards.yaml"), "standards")
    vendors = load_yaml_set(os.path.join(DICT_DIR, "vendors.yaml"), "vendors")
    component_types = load_yaml_set(os.path.join(DICT_DIR, "component_types.yaml"), "component_types")

    if GENERATE_DICT:
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

            save_yaml(os.path.join(DICT_DIR, "materials.yaml"), "materials", materials)
            save_yaml(os.path.join(DICT_DIR, "sizes.yaml"), "sizes", sizes)
            save_yaml(os.path.join(DICT_DIR, "standards.yaml"), "standards", standards)
            save_yaml(os.path.join(DICT_DIR, "vendors.yaml"), "vendors", vendors)
            save_yaml(os.path.join(DICT_DIR, "component_types.yaml"), "component_types", component_types)

        logging.info("Dictionary generation complete")

        print("Dictionary generation complete")

        subprocess.run(["python", os.path.join(ABBREV_DIR, "build_vendor_abbrev_map.py")])
        subprocess.run(["python", os.path.join(ABBREV_DIR, "build_standard_abbrev_map.py")])
        subprocess.run(["python", os.path.join(ABBREV_DIR, "build_component_abbrev_map.py")])
        subprocess.run(["python", os.path.join(ABBREV_DIR, "build_material_abbrev_map.py")])

    subprocess.run(["python", os.path.join(NORM_DIR, "normalize_vendors.py")])
    subprocess.run(["python", os.path.join(NORM_DIR, "normalize_standards.py")])
    subprocess.run(["python", os.path.join(NORM_DIR, "normalize_component_types.py")])
    subprocess.run(["python", os.path.join(NORM_DIR, "normalize_materials.py")])

    logging.info("All dictionaries normalized")
    print("All dictionaries normalized")


if __name__ == "__main__":
    main()
