import os
import json
import re

# Импорт функций ядра нормализации
from normalizer_core import (
    load_yaml_list,
    save_yaml,
    save_json,
    clean_token
)

# Импорт путей и настроек для компонентных типов
from scripts.config import (
    COMPONENT_RAW,
    COMPONENT_MAP,
    COMPONENT_CLEAN,
    COMPONENT_NOISE,
)

# Регулярные выражения для фильтрации токенов
DIGIT = re.compile(r"\d")  # Проверка наличия цифр
SIZE = re.compile(r"\b(UNC|UNF|UNRC|RF|FF|PSI|#)\b")  # Проверка признаков размеров
MATERIAL = re.compile(r"\b(SS|SST|WCB|CI|BRZ|BRONZE)\b")  # Проверка признаков материалов
MULTIWORD = re.compile(r"\s+")  # Проверка наличия пробелов
FORCE_NOISE = {"CSG", "CVB"}  # Принудительный шум


# Проверка валидности компонентного токена
def is_valid_component(token):
    t = token.upper()

    if DIGIT.search(t):
        return False  # Токен содержит цифры

    if SIZE.search(t):
        return False  # Токен похож на размер

    if MATERIAL.search(t):
        return False  # Токен похож на материал

    if MULTIWORD.search(t):
        return False  # Токен содержит пробелы

    if len(t) < 3:
        return False  # Слишком короткий токен

    return True


# Основная логика нормализации компонентных типов
def main():
    raw = load_yaml_list(COMPONENT_RAW, "component_types")  # Загрузка исходных типов

    if os.path.exists(COMPONENT_MAP):
        with open(COMPONENT_MAP, "r", encoding="utf-8") as f:
            abbrev = json.load(f)  # Загрузка маппинга сокращений
    else:
        abbrev = {"ASSY": "ASSEMBLY"}  # Базовый маппинг по умолчанию

    clean = set()  # Чистые токены
    noise = []  # Шумовые токены
    mapping_used = {}  # Использованные маппинги

    for item in raw:
        token = clean_token(item).upper()  # Очистка токена

        if token in FORCE_NOISE:
            noise.append(item)  # Принудительно отправляем в шум
            continue

        if token in abbrev:
            norm = abbrev[token].upper()  # Нормализация по маппингу
            mapping_used[item] = norm
            token = norm

        if is_valid_component(token):
            clean.add(token)  # Добавляем в чистые
        else:
            noise.append(item)  # Добавляем в шум

    save_yaml(COMPONENT_CLEAN, "component_types", sorted(clean))  # Сохранение чистых
    save_json(COMPONENT_NOISE, noise)  # Сохранение шума
    save_json(COMPONENT_MAP, mapping_used)  # Сохранение использованных маппингов

    print(f"Component types normalized. Clean {len(clean)}, noise {len(noise)}")


if __name__ == "__main__":
    main()
