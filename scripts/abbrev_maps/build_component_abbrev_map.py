import os
import json
import yaml
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")

from src.config import (
    COMPONENT_RAW,
    COMPONENT_MAP
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
    logging.info(f"Loaded {len(out)} RAW component tokens")
    return out


def call_llm(tokens):
    prompt = """ You are normalizing engineering component type abbreviations.

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
""" + str(tokens)

    return call_llm_mapping(prompt)


def call_llm_in_chunks(tokens):
    full_mapping = {}
    for i in range(0, len(tokens), CHUNK_SIZE):
        chunk = tokens[i:i+CHUNK_SIZE]
        logging.info(f"Processing component chunk {i}–{i+len(chunk)}")
        mapping = call_llm(chunk)
        full_mapping.update(mapping)
    return full_mapping


def main():
    tokens = load_yaml_list(COMPONENT_RAW, "component_types")
    mapping = call_llm_in_chunks(tokens)

    with open(COMPONENT_MAP, "w", encoding="utf8") as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)

    logging.info(f"Saved mapping: {COMPONENT_MAP}")


if __name__ == "__main__":
    main()
