import os
import json
import yaml
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")

from scripts.config import (
    VENDOR_RAW,
    VENDOR_MAP
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
    logging.info(f"Loaded {len(out)} RAW vendor tokens")
    return out


def call_llm(tokens):
    prompt = """
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

{
  "mapping": {
      "RAW_TOKEN": "NORMALIZED_VENDOR"
  }
}

RAW_TOKENS:
""" + str(tokens)

    return call_llm_mapping(prompt)


def call_llm_in_chunks(tokens):
    full_mapping = {}
    for i in range(0, len(tokens), CHUNK_SIZE):
        chunk = tokens[i:i+CHUNK_SIZE]
        logging.info(f"Processing vendor chunk {i}–{i+len(chunk)}")
        mapping = call_llm(chunk)
        full_mapping.update(mapping)
    return full_mapping


def main():
    tokens = load_yaml_list(VENDOR_RAW, "vendors")
    mapping = call_llm_in_chunks(tokens)

    with open(VENDOR_MAP, "w", encoding="utf8") as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)

    logging.info(f"Saved mapping: {VENDOR_MAP}")


if __name__ == "__main__":
    main()
