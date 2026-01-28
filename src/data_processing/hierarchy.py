import pandas as pd
import numpy as np
from typing import Dict, Optional
import logging
import time
import hashlib

logger = logging.getLogger(__name__)


# Обработчик иерархии BOM
class HierarchyProcessor:

    def __init__(self):
        logger.info("HierarchyProcessor initialized")
        self.stats: Dict = {}

    # основной конвейер обработки
    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        total_start = time.time()
        logger.info("Hierarchy: starting processing (%d rows)", len(df))

        df_h = df.copy()

        # исправление путей
        t = time.time()
        df_h = self._fix_paths(df_h)
        logger.info("Hierarchy: _fix_paths completed in %.3f sec", time.time() - t)

        # вычисление уровня иерархии
        t = time.time()
        df_h["abs_level"] = (
            df_h["path"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.count(r"\.")
        )
        logger.info("Hierarchy: abs_level computed in %.3f sec", time.time() - t)

        # извлечение parent_id
        t = time.time()
        df_h["parent_id"] = self._extract_parent_ids(df_h["path"])
        logger.info("Hierarchy: _extract_parent_ids completed in %.3f sec", time.time() - t)

        # определение типа узлов
        t = time.time()
        df_h = self._determine_node_types(df_h)
        logger.info("Hierarchy: _determine_node_types completed in %.3f sec", time.time() - t)

        # генерация уникальных идентификаторов
        t = time.time()
        df_h["unique_id"] = self._create_unique_ids(df_h)
        logger.info("Hierarchy: _create_unique_ids completed in %.3f sec", time.time() - t)

        # статистика использования
        t = time.time()
        df_h = self._calculate_usage_stats(df_h)
        logger.info("Hierarchy: _calculate_usage_stats completed in %.3f sec", time.time() - t)

        # построение числовой иерархии
        t = time.time()
        df_h = self._convert_to_numeric_hierarchy(df_h)
        logger.info("Hierarchy: _convert_to_numeric_hierarchy completed in %.3f sec", time.time() - t)

        # нормализация parent_id
        t = time.time()
        df_h = self._normalize_parent_ids(df_h)
        logger.info("Hierarchy: _normalize_parent_ids completed in %.3f sec", time.time() - t)

        logger.info(
            "Hierarchy: processing completed in %.3f sec (%d rows)",
            time.time() - total_start,
            len(df_h),
        )

        return df_h

    # исправление путей
    def _fix_paths(self, df: pd.DataFrame) -> pd.DataFrame:
        start = time.time()
        logger.info("Hierarchy: fixing paths")

        df_fixed = df.copy()

        paths = df_fixed["path"].fillna("").astype(str)
        paths = paths.str.strip(" .")

        for _ in range(3):
            paths = paths.str.replace(r"\.\.", ".", regex=True)

        def normalize_path(p: str) -> str:
            parts = [part.strip() for part in p.split(".") if part.strip()]
            return ".".join(parts)

        paths = paths.apply(normalize_path)
        df_fixed["path"] = paths

        changes = (df["path"].astype(str) != df_fixed["path"]).sum()
        self.stats["paths_fixed"] = int(changes)

        logger.info(
            "Hierarchy: path fixing completed (%d changed) in %.3f sec",
            changes,
            time.time() - start,
        )
        return df_fixed

    # извлечение parent_id
    @staticmethod
    def _extract_parent_ids(paths: pd.Series) -> pd.Series:
        paths = paths.fillna("").astype(str)
        has_parent = paths.str.contains(r"\.")
        parent = pd.Series([None] * len(paths), index=paths.index, dtype="object")

        split = paths[has_parent].str.rsplit(".", n=1).str[0]
        parent_ids = split.str.split(".").str[-1]

        parent.loc[has_parent] = parent_ids
        return parent

    # определение типа узлов
    def _determine_node_types(self, df: pd.DataFrame) -> pd.DataFrame:
        start = time.time()
        logger.info("Hierarchy: determining node types")

        df_t = df.copy()

        for col in ["is_assembly", "is_subassembly", "is_leaf"]:
            if col not in df_t.columns:
                df_t[col] = False

        df_t["is_assembly"] = df_t["abs_level"] == 0

        children_map = df_t["parent_id"].value_counts().to_dict()
        df_t["has_children"] = df_t["component_id"].astype(str).map(children_map).fillna(0) > 0

        df_t["is_leaf"] = ~df_t["has_children"]

        df_t["is_subassembly"] = df_t["has_children"] & (df_t["abs_level"] > 0)

        df_t["record_type"] = np.select(
            [
                df_t["is_assembly"],
                df_t["is_subassembly"],
                df_t["is_leaf"],
            ],
            [
                "ASSEMBLY",
                "SUBASSEMBLY",
                "LEAF",
            ],
            default="UNKNOWN",
        )

        logger.info(
            "Hierarchy: node types determined in %.3f sec", time.time() - start
        )
        return df_t

    # генерация уникальных идентификаторов
    @staticmethod
    def _create_unique_ids(df: pd.DataFrame) -> pd.Series:
        def make_uid(row):
            path_bytes = str(row["path"]).encode("utf-8")
            path_hash = hashlib.sha1(path_bytes).hexdigest()
            return f"{row['material_id']}_{row['component_id']}_{path_hash}"

        return df.apply(make_uid, axis=1)

    # статистика использования
    def _calculate_usage_stats(self, df: pd.DataFrame) -> pd.DataFrame:
        start = time.time()
        logger.info("Hierarchy: calculating usage statistics")

        df_u = df.copy()

        usage = df_u["component_id"].astype(str).value_counts()
        df_u["usage_count"] = df_u["component_id"].astype(str).map(usage)

        max_usage = df_u["usage_count"].max()
        df_u["usage_norm"] = (
            df_u["usage_count"] / max_usage if max_usage > 0 else 0.0
        )

        bins = [0, 1, 5, 20, 100, np.inf]
        labels = ["UNIQUE", "RARE", "COMMON", "FREQUENT", "VERY_FREQUENT"]
        df_u["usage_category"] = pd.cut(
            df_u["usage_count"],
            bins=bins,
            labels=labels,
            include_lowest=True,
            right=True,
        ).astype(str)

        logger.info(
            "Hierarchy: usage statistics completed in %.3f sec", time.time() - start
        )
        return df_u

    # построение числовой иерархии
    def _convert_to_numeric_hierarchy(self, df: pd.DataFrame) -> pd.DataFrame:
        df_n = df.copy()

        df_n = df_n.reset_index(drop=True)
        df_n["temp_id"] = df_n.index + 1

        comp_to_temp = dict(zip(df_n["component_id"], df_n["temp_id"]))

        def convert_path(p):
            if not p:
                return None
            parts = p.split(".")
            converted = [str(comp_to_temp.get(part)) for part in parts if part in comp_to_temp]
            return ".".join(converted) if converted else None

        df_n["numeric_path"] = df_n["path"].apply(convert_path)

        def extract_parent(npath):
            if not npath or "." not in npath:
                return None
            return int(npath.rsplit(".", 1)[0].split(".")[-1])

        df_n["parent_id"] = df_n["numeric_path"].apply(extract_parent)
        df_n["parent_id"] = df_n["parent_id"].apply(
            lambda x: str(int(x)) if pd.notna(x) else None
        )

        df_n["path"] = df_n["numeric_path"]
        df_n = df_n.drop(columns=["numeric_path"])

        return df_n

    # нормализация parent_id
    def _normalize_parent_ids(self, df: pd.DataFrame) -> pd.DataFrame:
        df_n = df.copy()

        valid_ids = set(df_n["temp_id"].astype(str))

        df_n["parent_id"] = df_n["parent_id"].apply(
            lambda pid: pid if pid in valid_ids else None
        )

        return df_n
