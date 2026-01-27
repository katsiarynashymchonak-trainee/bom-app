import os
from normalizer_core import (
    load_yaml_list,
    save_yaml,
    save_json,
    clean_token
)

# Импорт путей и настроек для нормализации материалов
from scripts.config import (
    MATERIAL_CLEAN,
    MATERIAL_MAP,
    MATERIAL_NOISE,
    MATERIAL_RAW,
    VENDOR_CLEAN,
    COMPONENT_CLEAN,
    STANDARD_CLEAN
)


# Загрузка значений из YAML в виде множества
def load_set(path, key):
    values = load_yaml_list(path, key)
    return {v.upper() for v in values}


# Основная логика нормализации материалов
def main():
    raw = load_yaml_list(MATERIAL_RAW, "materials")  # Загрузка исходных материалов

    vendors = load_set(VENDOR_CLEAN, "vendors")  # Загрузка списка вендоров
    components = load_set(COMPONENT_CLEAN, "component_types")  # Загрузка компонентных типов
    standards = load_set(STANDARD_CLEAN, "standards")  # Загрузка стандартов

    if os.path.exists(MATERIAL_MAP):
        import json
        with open(MATERIAL_MAP, "r", encoding="utf-8") as f:
            abbrev = json.load(f)  # Загрузка маппинга материалов
    else:
        abbrev = {}  # Пустой маппинг если файла нет

    clean = set()  # Чистые нормализованные материалы
    mapping = {}  # Использованные маппинги
    noise = []  # Шумовые значения

    for item in raw:
        token = clean_token(item).upper()  # Очистка токена

        if token in abbrev:
            norm = abbrev[token].upper()

            if norm in vendors or norm in components or norm in standards:
                noise.append(item)  # Если нормализация совпадает с вендором или компонентом
            else:
                mapping[item] = norm
                clean.add(norm)
            continue

        if token in vendors or token in components or token in standards:
            noise.append(item)  # Исключаем пересечения с другими словарями
            continue

        if len(token) >= 2:
            mapping[item] = token  # Добавляем как валидный материал
            clean.add(token)
        else:
            noise.append(item)  # Слишком короткие токены идут в шум

    save_yaml(MATERIAL_CLEAN, "materials", sorted(clean))  # Сохранение чистых материалов
    save_json(MATERIAL_MAP, mapping)  # Сохранение маппинга
    save_json(MATERIAL_NOISE, noise)  # Сохранение шума

    print(f"Materials normalized. Clean: {len(clean)}, noise: {len(noise)}")


if __name__ == "__main__":
    main()
