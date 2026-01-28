import json
import logging
import requests

from src.config import OLLAMA_URL, OLLAMA_MODEL


SYSTEM_PROMPT = """
You are a JSON-only normalization engine.

RULES:
1. You ALWAYS output STRICT VALID JSON.
2. NO explanations, NO markdown, NO comments.
3. NO text before or after JSON.
4. Output ONLY the JSON object required by the user prompt.
5. If the user prompt contains a JSON schema, you MUST follow it exactly.
6. If the user prompt contains RAW_TOKENS, you MUST return a JSON object with a "mapping" field.
7. NEVER wrap JSON in code fences.
8. NEVER add commentary, reasoning, or examples.
"""


def call_llm_mapping(prompt):
    logging.info("=== LLM PROMPT BEGIN ===")
    logging.info(prompt)
    logging.info("=== LLM PROMPT END ===")

    # Отправляет системный и пользовательский промпт
    try:
        resp = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "system": SYSTEM_PROMPT,
                "prompt": prompt
            },
            stream=True,
            timeout=60
        )
    except Exception as e:
        logging.error("LLM REQUEST FAILED: %s", str(e))
        return {}

    logging.info("HTTP STATUS: %s", resp.status_code)

    if resp.status_code != 200:
        logging.error("LLM returned non-200 status")
        logging.error(resp.text)
        return {}

    # Корректирует сырой ответ
    buffer = ""
    empty_stream = True

    for line in resp.iter_lines():
        empty_stream = False
        if not line:
            continue
        try:
            obj = json.loads(line.decode())
        except:
            continue

        if "response" in obj:
            buffer += obj["response"]

        if obj.get("done"):
            break

    if empty_stream:
        logging.error("LLM STREAM WAS EMPTY — NO DATA RECEIVED")
        return {}

    logging.info("=== RAW LLM OUTPUT BEGIN ===")
    logging.info(buffer)
    logging.info("=== RAW LLM OUTPUT END ===")

    # Парсинг JSON
    try:
        data = json.loads(buffer)
    except Exception as e:
        logging.error("JSON PARSE FAILED: %s", str(e))
        logging.error("RAW BUFFER WAS:")
        logging.error(buffer)
        return {}

    # Получение маппинга
    mapping = data.get("mapping", {})

    logging.info("=== FINAL MAPPING BEGIN ===")
    logging.info(str(mapping))
    logging.info("=== FINAL MAPPING END ===")

    # Нормализация
    out = {}
    for k, v in mapping.items():
        if not k or not v:
            continue
        out[str(k).strip().upper()] = str(v).strip().upper()

    return out
