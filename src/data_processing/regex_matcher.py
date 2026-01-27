import re
from dataclasses import dataclass
from typing import List, Dict


# Результат сопоставления по регулярным выражениям
@dataclass
class RegexMatchResult:
    values: List[str]
    confidences: Dict[str, float]
    sources: List[str]


# Единый мастер паттерн для всех типов признаков
MASTER_REGEX = re.compile(
    r"""
    (?P<size_triplet>\.?\d+(?:\.\d+)?\s*[xX]\s*\.?\d+(?:\.\d+)?\s*[xX]\s*\.?\d+(?:\.\d+)?)
    |
    (?P<size_pair>\.?\d+(?:\.\d+)?\s*[xX]\s*\.?\d+(?:\.\d+)?)
    |
    (?P<size_range>\.?\d+(?:\.\d+)?\s*[-/]\s*\.?\d+(?:\.\d+)?)
    |
    (?P<size_suffix>\.?\d+(?:\.\d+)?(?:DIA|OD|ID|SQ|T|P|THK|LG))
    |
    (?P<size_single>\.?\d+(?:\.\d+)?)
    |
    (?P<grade>A2-?\d*|A4-?\d*|8\.8|10\.9|12\.9|GRADE\s*\d+)
    |
    (?P<finish>ZINC|GALVANIZED|NICKEL|PAINTED|COATED|PASSIVATED|ANODIZED|PLATED|ZN)
    |
    (?P<thread>
        M\d{1,3}X\d+(?:\.\d+)? |
        M\d{1,3} |
        \#\d+ |
        UNC | UNF | UNRC |
        NPTF? | NPTM |
        10-32 |
        1/4-20
    )
    """,
    re.VERBOSE | re.IGNORECASE,
)


# Сопоставление признаков с помощью регулярных выражений
class RegexMatcher:

    def __init__(self):
        self.master = MASTER_REGEX
        self.standard_patterns = [
            re.compile(p, re.IGNORECASE)
            for p in [
                r"^ASTM[A-Z0-9\-]*$",
                r"^ASME[A-Z0-9\-]*$",
                r"^API[A-Z0-9\-]*$",
                r"^ISO[A-Z0-9\-]*$",
                r"^DIN[A-Z0-9\-]*$",
                r"^EN[A-Z0-9\-]*$",
                r"^NPTF?$",
                r"^UNC$",
                r"^UNF$",
                r"^UNRC$",
                r"^RTJ$",
                r"^RF\d*$",
                r"^FF\d*$",
                r"^SCH\d+$",
            ]
        ]

    # нормализация текста
    @staticmethod
    def _norm(text: str) -> str:
        return " ".join(str(text).upper().split())

    # единый метод извлечения всех признаков
    def match_all(self, text: str) -> Dict[str, RegexMatchResult]:
        t = self._norm(text)

        size_vals: List[str] = []
        size_conf: Dict[str, float] = {}

        grade_vals: List[str] = []
        finish_vals: List[str] = []
        thread_vals: List[str] = []

        for m in self.master.finditer(t):
            gd = m.groupdict()

            if gd.get("size_triplet"):
                v = gd["size_triplet"].upper()
                size_vals.append(v)
                size_conf[v] = max(size_conf.get(v, 0.0), 1.0)
                continue

            if gd.get("size_pair"):
                v = gd["size_pair"].upper()
                size_vals.append(v)
                size_conf[v] = max(size_conf.get(v, 0.0), 0.95)
                continue

            if gd.get("size_range"):
                v = gd["size_range"].upper()
                size_vals.append(v)
                size_conf[v] = max(size_conf.get(v, 0.0), 0.9)
                continue

            if gd.get("size_suffix"):
                v = gd["size_suffix"].upper()
                size_vals.append(v)
                size_conf[v] = max(size_conf.get(v, 0.0), 0.85)
                continue

            if gd.get("size_single"):
                v = gd["size_single"].upper()
                size_vals.append(v)
                size_conf[v] = max(size_conf.get(v, 0.0), 0.8)
                continue

            if gd.get("grade"):
                grade_vals.append(gd["grade"].upper())
                continue

            if gd.get("finish"):
                finish_vals.append(gd["finish"].upper())
                continue

            if gd.get("thread"):
                thread_vals.append(gd["thread"].upper())
                continue

        size_vals = list(dict.fromkeys(size_vals))
        grade_vals = list(dict.fromkeys(grade_vals))
        finish_vals = list(dict.fromkeys(finish_vals))
        thread_vals = list(dict.fromkeys(thread_vals))

        size_res = RegexMatchResult(
            size_vals,
            {v: size_conf.get(v, 0.8) for v in size_vals},
            ["regex_size"] if size_vals else [],
        )
        grade_res = RegexMatchResult(
            grade_vals,
            {v: 0.9 for v in grade_vals},
            ["regex"] if grade_vals else [],
        )
        finish_res = RegexMatchResult(
            finish_vals,
            {v: 0.8 for v in finish_vals},
            ["regex"] if finish_vals else [],
        )
        thread_res = RegexMatchResult(
            thread_vals,
            {v: 0.85 for v in thread_vals},
            ["regex"] if thread_vals else [],
        )

        std_vals: List[str] = []
        for token in t.split():
            for p in self.standard_patterns:
                if p.match(token):
                    std_vals.append(token.upper())
                    break
        std_vals = list(dict.fromkeys(std_vals))
        std_res = RegexMatchResult(
            std_vals,
            {v: 0.9 for v in std_vals},
            ["regex_strict"] if std_vals else [],
        )

        return {
            "size": size_res,
            "grade": grade_res,
            "finish": finish_res,
            "thread": thread_res,
            "strict_standard": std_res,
        }

    # отдельные методы для удобства
    def match_size(self, text: str) -> RegexMatchResult:
        return self.match_all(text)["size"]

    def match_grade(self, text: str) -> RegexMatchResult:
        return self.match_all(text)["grade"]

    def match_finish(self, text: str) -> RegexMatchResult:
        return self.match_all(text)["finish"]

    def match_thread(self, text: str) -> RegexMatchResult:
        return self.match_all(text)["thread"]

    def match_strict_standard(self, text: str) -> RegexMatchResult:
        return self.match_all(text)["strict_standard"]
