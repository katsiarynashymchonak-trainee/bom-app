import os
import yaml
import json
import re


# Блок очистки токенов и строк
def clean_token(tok: str) -> str:
    if not tok:
        return ""

    t = str(tok).upper()

    # Удаляем кавычки
    t = t.replace('"', " ").replace("'", " ")

    # Заменяем нижнее подчеркивание на пробел
    t = t.replace("_", " ")

    # Заменяем слеш и дефис на пробел
    t = t.replace("/", " ").replace("-", " ")

    # Удаляем повторяющиеся пробелы
    t = re.sub(r"\s+", " ", t).strip()

    return t


def clean_entry(entry: str) -> str:
    if not entry:
        return ""

    s = clean_token(entry)

    # Повторная очистка двойных пробелов
    s = re.sub(r"\s+", " ", s).strip()

    return s


# Блок загрузки YAML списков
def load_yaml_list(path: str, key: str) -> list:
    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
        raw = data.get(key, [])

    flat = []

    def flatten(x):
        if isinstance(x, list):
            for item in x:
                flatten(item)
        elif isinstance(x, dict) or x is None:
            return
        else:
            flat.append(clean_entry(str(x)))

    flatten(raw)
    return flat


# Блок загрузки YAML множеств
def load_yaml(path: str, key: str):

    if not os.path.exists(path):
        return set()

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
        raw = data.get(key, [])

    flat = set()

    def flatten(x):
        if isinstance(x, list):
            for item in x:
                flatten(item)
        elif isinstance(x, dict) or x is None:
            return
        else:
            flat.add(clean_entry(str(x)))

    flatten(raw)
    return flat


# Блок сохранения YAML и JSON
def save_yaml(path: str, key: str, values) -> None:
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump({key: sorted(values)}, f, allow_unicode=True, default_style=None)


def save_json(path: str, obj) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
