import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List

from .dictionary_matcher import DictionaryMatcher, MatchResult
from .regex_matcher import RegexMatcher, RegexMatchResult

logger = logging.getLogger(__name__)


@dataclass
class ParsedComponent:
    clean_name: str = ""
    component_type: str = ""
    material: str = ""
    size: str = ""
    vendor: str = ""
    standard: str = ""

    # новые флаги
    is_assembly: bool = False
    is_subassembly: bool = False
    is_leaf: bool = False

    # дополнительные данные
    additional_info: Dict[str, Any] = field(default_factory=dict)
    confidence_scores: Dict[str, float] = field(default_factory=dict)


class FeatureExtractor:
    """Извлечение признаков из описаний с помощью Aho–Corasick словарей и master‑regex."""

    def __init__(self):
        logger.info("FeatureExtractor initialized")
        self.dict_matcher = DictionaryMatcher()
        self.regex_matcher = RegexMatcher()
        self.stats = {
            "total": 0,
            "component_type": 0,
            "material": 0,
            "vendor": 0,
            "size": 0,
            "standard": 0,
        }

    @staticmethod
    def _normalize_description(text: str) -> str:
        return " ".join(str(text).strip().replace(",", ".").split())

    def parse_single(self, description: str) -> ParsedComponent:
        self.stats["total"] += 1

        text = self._normalize_description(description)
        logger.debug(f"[parse_single] Start parsing: '{text}'")

        info = ParsedComponent(clean_name=text)

        # Определение типа узла
        lower = text.lower()

        if any(w in lower for w in ["assembly", "сборка", "unit", "узел"]):
            info.is_assembly = True
        elif any(w in lower for w in ["subassembly", "подсборка"]):
            info.is_subassembly = True
        else:
            info.is_leaf = True

        try:
            dict_res: Dict[str, MatchResult] = self.dict_matcher.match_all(text)
            regex_res: Dict[str, RegexMatchResult] = self.regex_matcher.match_all(text)

            logger.debug(f"[parse_single] Dictionary results: {dict_res}")
            logger.debug(f"[parse_single] Regex results: {regex_res}")

            comp = dict_res["component_type"]
            mat = dict_res["material"]
            ven = dict_res["vendor"]
            std = dict_res["standard"]

            size = regex_res["size"]
            strict_std = regex_res["strict_standard"]

            # component_type
            if comp.values:
                info.component_type = " ".join(comp.values)
                self.stats["component_type"] += 1
                for v, c in comp.confidences.items():
                    info.confidence_scores[f"component_type:{v}"] = c

            # material
            if mat.values:
                info.material = " ".join(mat.values)
                self.stats["material"] += 1
                for v, c in mat.confidences.items():
                    info.confidence_scores[f"material:{v}"] = c

            # vendor
            if ven.values:
                info.vendor = " ".join(ven.values)
                self.stats["vendor"] += 1
                for v, c in ven.confidences.items():
                    info.confidence_scores[f"vendor:{v}"] = c

            # standards
            std_values = list(std.values)
            std_conf = dict(std.confidences)

            if strict_std.values:
                for v in strict_std.values:
                    if v not in std_values:
                        std_values.append(v)
                for v, c in strict_std.confidences.items():
                    std_conf[v] = max(std_conf.get(v, 0.0), c)

            if std_values:
                info.standard = " ".join(std_values)
                self.stats["standard"] += 1
                for v, c in std_conf.items():
                    info.confidence_scores[f"standard:{v}"] = c

            # size
            if size.values:
                info.size = " ".join(size.values)
                self.stats["size"] += 1
                for v, c in size.confidences.items():
                    info.confidence_scores[f"size:{v}"] = c

            # сохраняем исходный текст
            info.additional_info["raw"] = text

            # ограничение длины clean_name
            if len(info.clean_name) > 120:
                info.clean_name = info.clean_name[:120]

            logger.debug(f"[parse_single] Final parsed component: {info}")

        except Exception as e:
            logger.exception(f"[parse_single] Error parsing '{text}': {e}")

        return info

    def parse_batch(self, descriptions: List[str]) -> List[ParsedComponent]:
        logger.info(f"[parse_batch] Start batch parsing: {len(descriptions)} items")
        result = [self.parse_single(d) for d in descriptions]
        logger.info(f"[parse_batch] Finished batch parsing")
        return result

    def get_stats(self) -> Dict[str, Any]:
        logger.info(f"[get_stats] Stats: {self.stats}")
        return self.stats
