import os
import threading
import time
from typing import List

import torch
from sentence_transformers import SentenceTransformer
from sqlalchemy import func


# Сервис генерации эмбеддингов
class EmbeddingService:
    _instance = None
    _lock = threading.Lock()

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        os.environ["TOKENIZERS_PARALLELISM"] = "false"
        os.environ["TRANSFORMERS_CACHE"] = os.path.expanduser("~/.cache/huggingface")

        cache_dir = os.path.expanduser("~/.cache/sentence_transformers")

        self.model_name = model_name
        self.model = SentenceTransformer(
            model_name,
            cache_folder=cache_dir
        )

    @classmethod
    def instance(cls) -> "EmbeddingService":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    # кодирование одного текста
    def encode(self, text: str) -> List[float]:
        if not text:
            text = ""
        with torch.inference_mode():
            emb = self.model.encode(text, convert_to_numpy=True)
        return emb.tolist()

    # кодирование батча текстов
    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        texts = [t or "" for t in texts]
        with torch.inference_mode():
            embs = self.model.encode(
                texts,
                batch_size=256,
                show_progress_bar=False,
                convert_to_numpy=True
            )
        return [e.tolist() for e in embs]

    # пересборка всех эмбеддингов в БД
    def rebuild_embeddings(self, batch_size: int = 2000) -> dict:
        from src.db.database import SessionLocal
        from src.db.models import ComponentDB
        from src.core.chroma_repository import ChromaRepository
        from src.core.graph_service import GraphService

        chroma = ChromaRepository.instance()

        chroma_ids = chroma.get_all_ids()
        chroma_empty = len(chroma_ids) == 0

        chroma_meta = chroma.get_metadatas(chroma_ids) if not chroma_empty else {}
        chroma_updated = {
            uid: meta.get("updated_at")
            for uid, meta in chroma_meta.items()
        }

        session = SessionLocal()

        total = session.query(func.count(ComponentDB.id)).scalar()
        skipped = 0
        recomputed = 0

        offset = 0

        while True:
            t0 = time.time()
            batch_rows = (
                session.query(ComponentDB)
                .order_by(ComponentDB.id)
                .offset(offset)
                .limit(batch_size)
                .all()
            )
            t_load = time.time() - t0

            print(f"[EMB] Loaded batch in {t_load:.3f}s ({len(batch_rows)} rows)")

            if not batch_rows:
                break

            offset += batch_size

            to_recompute = []
            for r in batch_rows:
                uid = r.unique_id

                if chroma_empty:
                    to_recompute.append(r)
                    continue

                if r.embedding_vector is None:
                    to_recompute.append(r)
                    continue

                if uid not in chroma_updated:
                    to_recompute.append(r)
                    continue

                chroma_ts = chroma_updated.get(uid)
                sqlite_ts = r.updated_at.isoformat() if r.updated_at else None

                if sqlite_ts and chroma_ts and sqlite_ts > chroma_ts:
                    to_recompute.append(r)
                    continue

                skipped += 1

            if not to_recompute:
                continue

            texts = [(r.clean_name or "") for r in to_recompute]
            unique_ids = [r.unique_id for r in to_recompute]

            t1 = time.time()
            embeddings = self.encode_batch(texts)
            t_encode = time.time() - t1

            print(f"[EMB] encode_batch({len(texts)}) took {t_encode:.3f}s")

            now = func.now()

            t2 = time.time()
            for r, emb in zip(to_recompute, embeddings):
                r.embedding_vector = emb
                r.updated_at = now
            session.commit()
            t_commit = time.time() - t2

            print(f"[EMB] SQLite commit took {t_commit:.3f}s")

            metadatas = []
            for r in to_recompute:
                parts = r.unique_id.split(":", 2)
                material_id = parts[0] if len(parts) > 0 else None
                component_id = parts[1] if len(parts) > 1 else None
                path = parts[2] if len(parts) > 2 else None

                metadatas.append({
                    "unique_id": r.unique_id,
                    "material_id": material_id,
                    "component_id": component_id,
                    "path": path,
                    "abs_level": r.abs_level,
                    "is_assembly": r.is_assembly,
                    "is_subassembly": r.is_subassembly,
                    "is_leaf": r.is_leaf,
                    "updated_at": r.updated_at.isoformat() if r.updated_at else None,
                })

            t3 = time.time()
            chroma.upsert_batch(
                ids=unique_ids,
                embeddings=embeddings,
                metadatas=metadatas
            )
            t_chroma = time.time() - t3

            print(f"[EMB] Chroma upsert_batch({len(unique_ids)}) took {t_chroma:.3f}s")

            recomputed += len(to_recompute)

        session.close()

        GraphService._cache_graph = None
        GraphService._cache_hash = None

        return {
            "total": total,
            "recomputed": recomputed,
            "skipped": skipped,
            "chroma_empty": chroma_empty
        }
