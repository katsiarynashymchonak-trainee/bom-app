import pandas as pd
import numpy as np
from typing import Dict

from src.data_processing.hierarchy import HierarchyProcessor
from src.data_processing.feature_extractor import FeatureExtractor

import logging

logger = logging.getLogger(__name__)


# Обработчик для крупных BOM датасетов
class SimpleBOMProcessor:
    """Optimized processor for large BOM datasets (700k+ rows)."""

    def __init__(self, config_dir: str = "dictionaries", use_nlp: bool = False,
                 trained_models_dir: str = None):
        logger.info("Processor initialized")

        self.stats: Dict = {}
        self.processed_data: pd.DataFrame | None = None

        # иерархическая обработка
        self.hierarchy_processor = HierarchyProcessor()

        # извлечение признаков
        self.feature_extractor = FeatureExtractor()

        # информация о моделях
        self.stats["models"] = {
            "use_nlp": use_nlp,
            "has_pretrained_models": False,
            "config_dir": config_dir,
            "feature_extractor": "dictionary+regex",
        }

    # основной конвейер обработки
    def process_pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.info("Starting processing pipeline (%d rows)", len(df))

        df = self._validate_and_clean(df)
        df = self._parse_descriptions(df)
        df = self.hierarchy_processor.process(df)
        df = self._extract_features(df)

        logger.info("Skipping embedding generation (handled by API)")

        self.processed_data = df
        self.stats["final_rows"] = len(df)

        # статистика иерархии
        h_stats = self.hierarchy_processor.get_stats()
        self.stats["hierarchy"] = h_stats

        # распределение типов узлов
        dist = h_stats.get("record_type_distribution", {}) or {}

        self.stats["counts"] = {
            "assemblies": int(dist.get("ASSEMBLY", 0)),
            "subassemblies": int(dist.get("SUBASSEMBLY", 0)),
            "leafs": int(dist.get("LEAF", 0)),
            "total_nodes": sum(dist.values()),
        }

        logger.info(
            "Processing pipeline completed (%d rows) — assemblies: %d, subassemblies: %d, leafs: %d",
            len(df),
            self.stats["counts"]["assemblies"],
            self.stats["counts"]["subassemblies"],
            self.stats["counts"]["leafs"],
        )
        return df

    # проверка и очистка входных данных
    def _validate_and_clean(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.info("Validating and cleaning data")

        df = df.copy()

        required = ["material_id", "component_id", "description", "qty", "path"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        df = df.drop_duplicates(subset=["material_id", "component_id", "path"])

        df["path"] = df["path"].astype(str).str.strip()
        df = df[df["path"] != ""]

        parts = df["path"].str.split(".", expand=True)
        df["material_id"] = df["material_id"].fillna(parts[0])
        df["component_id"] = df["component_id"].fillna(parts[parts.columns[-1]])

        df["description"] = df["description"].fillna(df["component_id"]).fillna("NO_DESCRIPTION")

        df["qty"] = pd.to_numeric(df["qty"], errors="coerce").fillna(1.0)
        df["qty"] = df["qty"].clip(lower=0.001)

        logger.info("Cleaning completed (%d rows)", len(df))
        return df

    # парсинг описаний
    def _parse_descriptions(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.info("Parsing descriptions")

        df = df.copy()

        descriptions = df["description"].astype(str).tolist()
        components = self.feature_extractor.parse_batch(descriptions)

        df["clean_name"] = [c.clean_name for c in components]
        df["component_type"] = [c.component_type for c in components]
        df["material"] = [c.material for c in components]
        df["size"] = [c.size for c in components]
        df["vendor"] = [c.vendor for c in components]
        df["standard"] = [c.standard for c in components]

        # новые флаги
        df["is_assembly"] = [c.is_assembly for c in components]
        df["is_subassembly"] = [c.is_subassembly for c in components]
        df["is_leaf"] = [c.is_leaf for c in components]

        logger.info("Description parsing completed")
        return df

    # извлечение дополнительных признаков
    def _extract_features(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.info("Extracting features")

        df = df.copy()

        df["embedding_text"] = (
            df["clean_name"].fillna("") + ". " +
            "Type: " + df["component_type"].fillna("") + ". " +
            "Material: " + df["material"].fillna("") + ". " +
            "Size: " + df["size"].fillna("") + ". " +
            "Vendor: " + df["vendor"].fillna("")
        ).str.strip()

        df["search_text"] = (
            df["component_id"].astype(str) + " " +
            df["clean_name"].fillna("") + " " +
            df["component_type"].fillna("") + " " +
            df["vendor"].fillna("")
        ).str.strip()

        df["qty_log"] = np.log1p(df["qty"])

        logger.info("Feature extraction completed")
        return df

    # публичные методы
    def get_stats(self) -> Dict:
        return self.stats

    def get_processed_data(self) -> pd.DataFrame:
        return self.processed_data
