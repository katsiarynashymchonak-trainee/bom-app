import os
import json
import logging

# Импорт путей
from src.config import (
    DICT_DIR,
    COMPONENT_RAW,
    COMPONENT_CLEAN,
    COMPONENT_NOISE,
    COMPONENT_MAP,
    MATERIAL_RAW,
    MATERIAL_CLEAN,
    MATERIAL_NOISE,
    MATERIAL_MAP,
    VENDOR_RAW,
    VENDOR_CLEAN,
    VENDOR_NOISE,
    VENDOR_MAP,
    STANDARD_RAW,
    STANDARD_CLEAN,
    STANDARD_NOISE,
    STANDARD_MAP,
)
from scripts.normalization.normalizer_core import load_yaml_list

# Настройки логирования
LOG_PATH = os.path.join(DICT_DIR, "dictionary_metrics.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, mode="w", encoding="utf-8"),
        logging.StreamHandler()
    ]
)


# Загрузка JSON списка
def load_json_list(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [str(x).strip() for x in json.load(f)]


# Загрузка JSON словаря
def load_json_map(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {str(k).strip(): str(v).strip() for k, v in data.items()}


# Класс для оценки качества словарей
class DictionaryEvaluator:

    # Инициализация
    def __init__(self):
        self.categories = {
            "materials": (MATERIAL_RAW, MATERIAL_CLEAN, MATERIAL_NOISE, MATERIAL_MAP),
            "vendors": (VENDOR_RAW, VENDOR_CLEAN, VENDOR_NOISE, VENDOR_MAP),
            "standards": (STANDARD_RAW, STANDARD_CLEAN, STANDARD_NOISE, STANDARD_MAP),
            "component_types": (COMPONENT_RAW, COMPONENT_CLEAN, COMPONENT_NOISE, COMPONENT_MAP),
        }

    # Подсчёт метрик для одной категории
    def evaluate_category(self, name, paths):
        raw_path, clean_path, noise_path, map_path = paths

        raw = load_yaml_list(raw_path, name)
        clean = load_yaml_list(clean_path, name)
        noise = load_json_list(noise_path)
        mapping = load_json_map(map_path)

        total = len(clean) + len(noise)
        coverage = len(clean) / total if total > 0 else 0
        noise_ratio = len(noise) / total if total > 0 else 0
        mapping_completeness = len(mapping) / len(clean) if len(clean) > 0 else 0

        unmapped = sorted([t for t in clean if t not in mapping])

        result = {
            "category": name,
            "raw_count": len(raw),
            "clean_count": len(clean),
            "noise_count": len(noise),
            "mapping_count": len(mapping),
            "coverage": coverage,
            "noise_ratio": noise_ratio,
            "mapping_completeness": mapping_completeness,
            "unmapped_tokens": unmapped,
        }

        logging.info(f"--- {name.upper()} ---")
        logging.info(f"Raw tokens: {result['raw_count']}")
        logging.info(f"Clean tokens: {result['clean_count']}")
        logging.info(f"Noise tokens: {result['noise_count']}")
        logging.info(f"Mapping entries: {result['mapping_count']}")
        logging.info(f"Coverage: {result['coverage']:.3f}")
        logging.info(f"Noise ratio: {result['noise_ratio']:.3f}")
        logging.info(f"Mapping completeness: {result['mapping_completeness']:.3f}")

        return result

    # Основной метод запуска
    def run(self):
        logging.info("=== Dictionary Quality Evaluation Started ===")

        results = {}
        for name, paths in self.categories.items():
            results[name] = self.evaluate_category(name, paths)

        logging.info("=== Evaluation complete ===")
        return results


# Точка входа для запуска как скрипта
if __name__ == "__main__":
    evaluator = DictionaryEvaluator()
    evaluator.run()
