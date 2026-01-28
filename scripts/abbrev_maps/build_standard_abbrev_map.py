import os
import json
import yaml
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")

from src.config import (
    STANDARD_RAW,
    STANDARD_MAP
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
    logging.info(f"Loaded {len(out)} RAW standard tokens")
    return out


def call_llm(tokens):
    prompt = """
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

{
  "mapping": {
      "RAW_TOKEN": "BASE_STANDARD"
  }
}

RAW_TOKENS:
""" + str(tokens)

    return call_llm_mapping(prompt)


def call_llm_in_chunks(tokens):
    full_mapping = {}
    for i in range(0, len(tokens), CHUNK_SIZE):
        chunk = tokens[i:i+CHUNK_SIZE]
        logging.info(f"Processing standard chunk {i}–{i+len(chunk)}")
        mapping = call_llm(chunk)
        full_mapping.update(mapping)
    return full_mapping


def main():
    tokens = load_yaml_list(STANDARD_RAW, "standards")
    mapping = call_llm_in_chunks(tokens)

    with open(STANDARD_MAP, "w", encoding="utf8") as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)

    logging.info(f"Saved mapping: {STANDARD_MAP}")


if __name__ == "__main__":
    main()
