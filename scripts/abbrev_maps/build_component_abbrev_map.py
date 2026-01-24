import os
import json
import yaml
import requests

# Импорт путей и настроек для нормализации компонентных типов
from scripts.config import (
    COMPONENT_CLEAN,
    COMPONENT_MAP,
    OLLAMA_MODEL,
    OLLAMA_URL
)


# Загрузка списка компонентных типов из YAML с разворачиванием вложенных структур
def load_yaml_list(path, key):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf8") as f:
        data = yaml.safe_load(f) or {}  # Загружаем YAML, если пустой — подставляем {}
        raw = data.get(key, [])  # Берём список по ключу
    out = []

    def flatten(x):
        # Рекурсивно разворачиваем вложенные списки
        if isinstance(x, list):
            for i in x:
                flatten(i)
        elif isinstance(x, dict) or x is None:
            return  # Игнорируем словари и None
        else:
            out.append(str(x).strip().upper())  # Приводим к строке и верхнему регистру

    flatten(raw)
    return out


# Вызов LLM для нормализации компонентных типов
def call_llm(tokens):
    prompt = f"""
You are normalizing engineering component type abbreviations.

Your task for EACH RAW token:

1. Expand abbreviations into full engineering component terms.
   Examples:
     ASSY → ASSEMBLY
     BRG → BEARING
     SHFT → SHAFT
     RTR / ROTR / ROTORS → ROTOR
     SHCS / HHCS / SQHSS → SCREW
     COV → COVER
     DRAINS → DRAIN
     BOLTING → BOLT
     BUSH → BUSHING
     HANDVALVE → VALVE
     TURB → TURBINE

2. Detect and split concatenated component terms.
   You MUST insert missing spaces when multiple known engineering component words appear inside one token.
   Known component vocabulary includes (but is not limited to):
     BEARING, BALL, BODY, BONNET, BOLT, BUSHING, GEAR, BOX, TURBINE, BUCKET,
     SOLENOID, CAGE, GAUGE, SHAFT, CONDENSER, CONTROLLER, ENCLOSURE, COOLER,
     PINION, SPUR, GLAND, PIN, TAPPET, GASKET, INDICATOR, IMPELLER, SEAL,
     SWITCH, NIPPLE, PURGE, PRESS, PORT, TRANSDUCER, SENSOR, PROBE, SCREEN,
     SEAT, SIGNAL, SILENCER, VENT, SLEEVE, THRUST, TUBE, TRANSMITTER,
     ASSEMBLY, COLLAR, RING, STUD, SPRING, SPACER, HOUSING, PIPE, UNION,
     ELBOW, FITTING, FLANGE, GASKET, VALVE, NOZZLE, WHEEL, KEY, LEVER, LINKAGE and others

   Examples:
     BOLTTRIPCOLLARASSY → BOLT TRIP COLLAR ASSEMBLY
     BEARINGHOUSING → BEARING HOUSING
     TURBGEARBOX → TURBINE GEAR BOX
     SPACERBEARINGSET → SPACER BEARING SET

3. After expansion and splitting, match the resulting words ONLY to canonical component types from the provided list.
   The canonical list is the ONLY allowed vocabulary.
   If a word is not in the canonical list, you must NOT use it.

4. If multiple canonical matches are possible, choose the most specific or most complete canonical type.

5. If no canonical match exists, skip the token.

6. Do NOT invent new component types.
   Do NOT guess.
   Do NOT create synonyms.
   Do NOT output anything not present in the canonical list.

7. Exclude and ignore:
   - vendors or brands (SKF, ABB, BENTLEY, EMERSON, SIEMENS, etc.)
   - materials (STAINLESS STEEL, WCB, BRONZE, etc.)
   - standards (API, ASME, ASTM, ISO, DIN, NPT, etc.)
   - sizes or numeric codes (3/4, 150RF, 1IN, 2X3, etc.)
   - operations (MACHINING, WELDMENT, REBUILD)
   - parameters (RPM, PSI, DEG, etc.)

Return STRICT JSON ONLY:
{
  "mapping": {
      "RAW_TOKEN": "CANONICAL_COMPONENT_TYPE"
  }
}

Canonical component types:
{tokens}

Raw tokens:
{tokens}

"""

    resp = requests.post(
        OLLAMA_URL,
        json={"model": OLLAMA_MODEL, "prompt": prompt},
        stream=True  # Потоковый режим — LLM присылает ответ частями
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

    # Поиск первого и последнего символа JSON
    start = buffer.find("{")
    end = buffer.rfind("}")
    if start == -1 or end == -1:
        return {}  # Если JSON не найден — возвращаем пустой словарь

    data = json.loads(buffer[start:end + 1].replace("'", '"'))  # Приводим к валидному JSON
    mapping = data.get("mapping", {}) or {}

    return {k.upper(): v.upper() for k, v in mapping.items()}  # Приводим ключи и значения к верхнему регистру


# Основная функция: загрузка токенов, нормализация, сохранение результата
def main():
    tokens = load_yaml_list(COMPONENT_CLEAN, "component_types")  # Загружаем очищенные типы компонентов
    mapping = call_llm(tokens)  # Нормализуем через LLM

    with open(COMPONENT_MAP, "w", encoding="utf8") as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)  # Сохраняем JSON-маппинг

    print("Saved", COMPONENT_MAP)


if __name__ == "__main__":
    main()
