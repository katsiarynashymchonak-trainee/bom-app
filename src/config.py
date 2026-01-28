# bom_app/src/config.py
import os

# Основные настройки
GENERATE_DICT = False
CREATE_ABBREV_MAPS = False
NORM_DICTS = True

# Базовые директории
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
DICT_DIR = os.environ.get("DICT_DIR", os.path.join(ROOT_DIR, "dictionaries"))

# Путь к файлу уникальных описаний
DESCRIPTIONS_PATH = os.environ.get("DESCRIPTIONS_PATH", os.path.join(DICT_DIR, "unique_descriptions.csv"))

# Пути к папкам с данными
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(ROOT_DIR, "data"))
CHROMA_DIR = os.environ.get("CHROMA_DIR", os.path.join(DATA_DIR, "chroma"))
RAW_DATA_DIR = os.environ.get("RAW_DATA_DIR", os.path.join(DATA_DIR, "raw"))
PROCESSED_DATA_DIR = os.environ.get("PROCESSED_DATA_DIR", os.path.join(DATA_DIR, "processed"))


# Пути к raw‑данным
COMPONENT_RAW = os.environ.get("COMPONENT_RAW", os.path.join(DICT_DIR, "component_types.yaml"))
MATERIAL_RAW = os.environ.get("MATERIAL_RAW", os.path.join(DICT_DIR, "materials.yaml"))
STANDARD_RAW = os.environ.get("STANDARD_RAW", os.path.join(DICT_DIR, "standards.yaml"))
VENDOR_RAW = os.environ.get("VENDOR_RAW", os.path.join(DICT_DIR, "vendors.yaml"))
SIZES_RAW = os.environ.get("SIZES_RAW", os.path.join(DICT_DIR, "sizes.yaml"))

# Пути к очищенным данным
CLEAN_DIR = os.environ.get("CLEAN_DIR", os.path.join(DICT_DIR, "clean"))
COMPONENT_CLEAN = os.environ.get("COMPONENT_CLEAN", os.path.join(CLEAN_DIR, "component_types_clean.yaml"))
MATERIAL_CLEAN = os.environ.get("MATERIAL_CLEAN", os.path.join(CLEAN_DIR, "materials_clean.yaml"))
VENDOR_CLEAN = os.environ.get("VENDOR_CLEAN", os.path.join(CLEAN_DIR, "vendors_clean.yaml"))
STANDARD_CLEAN = os.environ.get("STANDARD_CLEAN", os.path.join(CLEAN_DIR, "standards_clean.yaml"))

# Пути к шумовым данным
NOISE_DIR = os.environ.get("NOISE_DIR", os.path.join(DICT_DIR, "noise"))
COMPONENT_NOISE = os.environ.get("COMPONENT_NOISE", os.path.join(NOISE_DIR, "component_types_noise.json"))
MATERIAL_NOISE = os.environ.get("MATERIAL_NOISE", os.path.join(NOISE_DIR, "materials_noise.json"))
VENDOR_NOISE = os.environ.get("VENDOR_NOISE", os.path.join(NOISE_DIR, "vendors_noise.json"))
STANDARD_NOISE = os.environ.get("STANDARD_NOISE", os.path.join(NOISE_DIR, "standards_noise.json"))

# Пути к маппингам
MAPPING_DIR = os.environ.get("MAPPING_DIR", os.path.join(DICT_DIR, "mapping"))
COMPONENT_MAP = os.environ.get("COMPONENT_MAP", os.path.join(MAPPING_DIR, "component_abbrev_map.json"))
MATERIAL_MAP = os.environ.get("MATERIAL_MAP", os.path.join(MAPPING_DIR, "materials_abbrev_map.json"))
VENDOR_MAP = os.environ.get("VENDOR_MAP", os.path.join(MAPPING_DIR, "vendors_abbrev_map.json"))
STANDARD_MAP = os.environ.get("STANDARD_MAP", os.path.join(MAPPING_DIR, "standards_abbrev_map.json"))

# Настройки Ollama
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1")