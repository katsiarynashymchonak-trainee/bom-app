import os
import json
import re

from normalizer_core import (
    load_yaml_list,
    save_yaml,
    save_json,
    clean_token
)

from src.config import (
    COMPONENT_RAW,
    COMPONENT_MAP,
    COMPONENT_CLEAN,
    COMPONENT_NOISE,
)

# Канонический список должен быть всегда включён в CLEAN
CANONICAL_COMPONENT_TYPES = {
    "ACTUATOR", "ADAPTER", "ANGLE", "ASSEMBLY", "BEARING", "BLADE", "BOLT", "BOLTING",
    "BRACKET", "BUSHING", "BUSH", "CAPSCREW", "CASE", "CASING", "COLLAR", "CONNECTOR",
    "COUPLING", "COVER", "CYLINDER", "DRAIN", "ELBOW", "FITTING", "FLANGE", "GASKET",
    "GAUGE", "GAUGEBOARD", "GOVERNOR", "HANDLE", "HARDWARE", "HOUSING", "INLET", "KEY",
    "LABYRINTH", "LEAKOFF", "LEVER", "LINKAGE", "LOCKNUT", "LOCKWASHER", "LUBRICATION",
    "MOUNTING", "NAMEPLATE", "NIPPLE", "NOZZLE", "NUT", "ORIFICE", "PACKING", "PIPE",
    "PIPEGUARD", "PIPEPLUG", "PIPING", "PUMP", "REDUCER", "RING", "ROLLPIN", "ROTATION",
    "ROTOR", "SCREW", "SEAL", "SEALANT", "SECTOR", "SETSCREW", "SHAFT", "SHROUDBAND",
    "SHSS", "SIPHON", "SOLENOID", "SOLEPLATE", "SPACER", "SPRING", "STEM", "STUD",
    "TACHOMETER", "TAPPET", "TEE", "THERMOMETER", "THROTTLE", "TRIP", "TRUNNION",
    "TURBINE", "TURB", "UNION", "VALVE", "WASHER", "WHEEL", "BODY", "BONNET", "GEAR",
    "BOX", "BUCKET", "BUMPER", "CAGE", "BORD", "CIRC", "CLAPPER", "CONDENSER", "EJECTOR",
    "TRANSFORMER", "CONTROLLER", "ENCLOSURE", "EYEBOLT", "STUB", "COOLER", "LUBE",
    "PINION", "SPUR", "GLAND", "PIN", "INDICATOR", "IMPELLER", "BLANKET", "SWITCH",
    "PURGE", "PRESS", "PORT", "SOFTWARE", "TRANSDUCER", "SENSOR", "PROBE", "STK",
    "SCREEN", "SEAT", "SET", "SIGNAL", "SILENCER", "VENT", "SLEEVE", "THRUST", "TUBE",
    "VELOMITOR", "TRANSMITTER", "WARNING", "WATER COOL"
}

DIGIT = re.compile(r"\d")
SIZE = re.compile(r"\b(UNC|UNF|UNRC|RF|FF|PSI|#)\b")
MATERIAL = re.compile(r"\b(SS|SST|WCB|CI|BRZ|BRONZE|STEEL)\b")
MULTIWORD = re.compile(r"\s+")
FORCE_NOISE = {"CSG", "CVB"}


def is_valid_component(token):
    t = token.upper()

    if t in CANONICAL_COMPONENT_TYPES:
        return True

    if DIGIT.search(t):
        return False

    if SIZE.search(t):
        return False

    if MATERIAL.search(t):
        return False

    if MULTIWORD.search(t):
        return False

    if len(t) < 3:
        return False

    return True


def main():
    raw = load_yaml_list(COMPONENT_RAW, "component_types")

    if os.path.exists(COMPONENT_MAP):
        with open(COMPONENT_MAP, "r", encoding="utf-8") as f:
            abbrev = json.load(f)
    else:
        abbrev = {"ASSY": "ASSEMBLY"}

    clean = set(CANONICAL_COMPONENT_TYPES)
    noise = []
    mapping_used = {}

    for item in raw:
        token = clean_token(item).upper()

        if token in FORCE_NOISE:
            noise.append(item)
            continue

        if token in abbrev:
            norm = abbrev[token].upper()
            mapping_used[item] = norm
            token = norm

        if is_valid_component(token):
            clean.add(token)
        else:
            noise.append(item)

    save_yaml(COMPONENT_CLEAN, "component_types", sorted(clean))
    save_json(COMPONENT_NOISE, noise)
    save_json(COMPONENT_MAP, mapping_used)

    print(f"Component types normalized. Clean {len(clean)}, noise {len(noise)}")


if __name__ == "__main__":
    main()
