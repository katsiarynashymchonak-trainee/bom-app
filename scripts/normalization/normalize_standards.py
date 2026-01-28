import os
import re
from normalizer_core import (
    load_yaml_list,
    save_yaml,
    save_json,
    clean_token
)

# Импорт путей и настроек для нормализации стандартов
from src.config import (
    STANDARD_RAW,
    STANDARD_MAP,
    STANDARD_CLEAN,
    STANDARD_NOISE
)


# Регулярные выражения для определения очевидных стандартов
STD_PATTERNS = [
    r"^ASTM(\s+[A-Z]\d+.*)?$",
    r"^ASME(\s+[A-Z]\d+.*)?$",
    r"^API(\s*\d+[A-Z]?)?$",
    r"^ISO(\s*\d+.*)?$",
    r"^DIN(\s*\d+.*)?$",
    r"^EN(\s*\d+.*)?$",
    r"^NPTF?$",
    r"^NPTM$",
    r"^UNC(\s*[-]?\s*\d+[A-Z]?)?$",
    r"^UNF(\s*[-]?\s*\d+[A-Z]?)?$",
    r"^UNRC$",
    r"^RTJ$",
    r"^RF\d*$",
    r"^FF\d*$",
    r"^SCH\s*\d+$",
    r"^SCH\d+$",
]


# Проверка что токен соответствует одному из шаблонов стандартов
def is_standard(token):
    """Return True if token matches any strict standard regex."""
    for p in STD_PATTERNS:
        if re.match(p, token):
            return True
    return False


# Основная логика нормализации стандартов
def main():
    raw = load_yaml_list(STANDARD_RAW, "standards")  # Загрузка исходных стандартов

    if os.path.exists(STANDARD_MAP):
        import json
        with open(STANDARD_MAP, "r", encoding="utf-8") as f:
            abbrev = json.load(f)  # Загрузка маппинга от LLM
    else:
        abbrev = {}  # Пустой маппинг если файла нет

    clean = set()  # Чистые стандарты
    mapping = {}  # Использованные маппинги
    noise = []  # Шумовые значения

    for item in raw:
        token = clean_token(item).upper()  # Очистка токена

        if token in abbrev:
            norm = abbrev[token].upper()  # Используем нормализацию от LLM
            mapping[item] = norm
            clean.add(norm)
            continue

        if is_standard(token):
            mapping[item] = token  # Добавляем как валидный стандарт
            clean.add(token)
        else:
            noise.append(item)  # Всё остальное идёт в шум

    save_yaml(STANDARD_CLEAN, "standards", sorted(clean))  # Сохранение чистых стандартов
    save_json(STANDARD_MAP, mapping)  # Сохранение маппинга
    save_json(STANDARD_NOISE, noise)  # Сохранение шума

    print(f"Standards normalized. Clean: {len(clean)}, noise: {len(noise)}")


if __name__ == "__main__":
    main()
