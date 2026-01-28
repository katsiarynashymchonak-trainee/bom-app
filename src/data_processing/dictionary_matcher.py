import os
import re
import yaml
import ahocorasick
from dataclasses import dataclass
from typing import List, Dict

from src.config import (
    COMPONENT_CLEAN,
    MATERIAL_CLEAN,
    VENDOR_CLEAN,
    STANDARD_CLEAN,
)


@dataclass
class MatchResult:
    values: List[str]
    confidences: Dict[str, float]
    sources: List[str]


def _load_yaml_list(path: str, key: str) -> List[str]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return [str(v).strip().upper() for v in data.get(key, [])]


class DictionaryMatcher:
    """
    Dictionary-based matching for component_type, material, vendor, standard
    с использованием Aho–Corasick (один проход по строке).
    """

    def __init__(self):
        self.component_types = _load_yaml_list(COMPONENT_CLEAN, "component_types")
        self.materials = _load_yaml_list(MATERIAL_CLEAN, "materials")
        self.vendors = _load_yaml_list(VENDOR_CLEAN, "vendors")
        self.standards = _load_yaml_list(STANDARD_CLEAN, "standards")

        self.automaton = ahocorasick.Automaton()

        for token in self.component_types:
            self.automaton.add_word(token, ("component_type", token))

        for token in self.materials:
            self.automaton.add_word(token, ("material", token))

        for token in self.vendors:
            self.automaton.add_word(token, ("vendor", token))

        for token in self.standards:
            self.automaton.add_word(token, ("standard", token))

        self.automaton.make_automaton()

    @staticmethod
    def _normalize_text(text: str) -> str:
        return re.sub(r"\s+", " ", str(text).strip()).upper()

    def match_all(self, text: str) -> Dict[str, MatchResult]:
        norm = self._normalize_text(text)

        results: Dict[str, MatchResult] = {
            "component_type": MatchResult([], {}, []),
            "material": MatchResult([], {}, []),
            "vendor": MatchResult([], {}, []),
            "standard": MatchResult([], {}, []),
        }

        for _, (label, token) in self.automaton.iter(norm):
            r = results[label]
            val = token.upper()
            if val not in r.values:
                r.values.append(val)
            r.confidences[val] = max(r.confidences.get(val, 0.0), 0.95)
            if "dict" not in r.sources:
                r.sources.append("dict")

        return results

    # удобные обёртки, если где-то ещё используется старый интерфейс

    def match_component_type(self, text: str) -> MatchResult:
        return self.match_all(text)["component_type"]

    def match_material(self, text: str) -> MatchResult:
        return self.match_all(text)["material"]

    def match_vendor(self, text: str) -> MatchResult:
        return self.match_all(text)["vendor"]

    def match_standard(self, text: str) -> MatchResult:
        return self.match_all(text)["standard"]
