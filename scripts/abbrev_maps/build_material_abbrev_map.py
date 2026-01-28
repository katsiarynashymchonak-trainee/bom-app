import os
import json
import yaml
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")

from src.config import (
    MATERIAL_RAW,
    MATERIAL_MAP
)

from scripts.llm.llm_utils import call_llm_mapping

CHUNK_SIZE = 150


def load_yaml_list(path, key):
    if not os.path.exists(path):
        logging.warning(f"YAML file not found: {path}")
        return []
    with open(path, "r", encoding="utf8") as f:
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
    logging.info(f"Loaded {len(out)} RAW material tokens")
    return out


def call_llm(tokens):
    prompt = """
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

{
  "mapping": {
      "RAW_TOKEN": "NORMALIZED_MATERIAL"
  }
}

RAW_TOKENS:
""" + str(tokens)

    return call_llm_mapping(prompt)


def call_llm_in_chunks(tokens):
    full_mapping = {}
    for i in range(0, len(tokens), CHUNK_SIZE):
        chunk = tokens[i:i+CHUNK_SIZE]
        logging.info(f"Processing material chunk {i}–{i+len(chunk)}")
        mapping = call_llm(chunk)
        full_mapping.update(mapping)
    return full_mapping


def main():
    tokens = load_yaml_list(MATERIAL_RAW, "materials")
    mapping = call_llm_in_chunks(tokens)

    with open(MATERIAL_MAP, "w", encoding="utf8") as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)

    logging.info(f"Saved mapping: {MATERIAL_MAP}")


if __name__ == "__main__":
    main()
