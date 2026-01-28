import os
from normalizer_core import (
    load_yaml_list,
    save_yaml,
    save_json,
    clean_token
)
from src.config import VENDOR_RAW, VENDOR_MAP, VENDOR_CLEAN, VENDOR_NOISE


# Основная логика нормализации вендоров
def main():
    raw = load_yaml_list(VENDOR_RAW, "vendors")  # Загрузка исходного списка вендоров

    if os.path.exists(VENDOR_MAP):
        import json
        with open(VENDOR_MAP, "r", encoding="utf-8") as f:
            abbrev = json.load(f)  # Загрузка маппинга от LLM
    else:
        abbrev = {}  # Пустой маппинг если файл отсутствует

    clean = set()  # Чистые нормализованные вендоры
    mapping = {}  # Использованные маппинги
    noise = []  # Шумовые значения

    for item in raw:
        token = clean_token(item).upper()  # Очистка токена

        if token in abbrev:
            norm = abbrev[token].upper()  # Используем нормализацию от LLM
            mapping[item] = norm
            clean.add(norm)
            continue

        noise.append(item)  # Всё что не распознано идёт в шум

    save_yaml(VENDOR_CLEAN, "vendors", sorted(clean))  # Сохранение чистых вендоров
    save_json(VENDOR_MAP, mapping)  # Сохранение маппинга
    save_json(VENDOR_NOISE, noise)  # Сохранение шума

    print(f"Vendors normalized. Clean: {len(clean)}, noise: {len(noise)}")


if __name__ == "__main__":
    main()
