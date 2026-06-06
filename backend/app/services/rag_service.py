import hashlib
import os
from typing import Optional
from pathlib import Path

from app.core.logging_config import get_logger

logger = get_logger(__name__)

_faiss = None
np = None
_faiss_available = False
_fastembed_available = False
_fastembed_model = None


def _try_init_faiss() -> bool:
    global _faiss, np, _faiss_available
    if _faiss_available:
        return True
    try:
        import faiss as _faiss_mod
        import numpy as np_mod
        _faiss = _faiss_mod
        np = np_mod
        _faiss_available = True
    except ImportError:
        logger.warning("faiss or numpy not available, RAG will use long-context fallback")
    return _faiss_available


def _try_import_fastembed() -> bool:
    global _fastembed_available
    if _fastembed_available:
        return True
    try:
        from fastembed import TextEmbedding
        import fastembed.common.model_management as _mm
        import huggingface_hub
        from dataclasses import dataclass

        # Monkey-patch snapshot_download to bypass HF SSL cert issues behind proxy
        _orig_snapshot = _mm.snapshot_download
        def _patched_snapshot(repo_id, **kwargs):
            base_cache = kwargs.get("cache_dir", os.path.expanduser("~/.cache/fastembed"))
            snap_base = os.path.join(
                base_cache, f"models--{repo_id.replace('/', '--')}", "snapshots"
            )
            if os.path.isdir(snap_base):
                snaps = os.listdir(snap_base)
                if snaps:
                    return os.path.join(snap_base, snaps[0])
            return _orig_snapshot(repo_id, **kwargs)
        _mm.snapshot_download = _patched_snapshot

        @dataclass
        class _MockInfo:
            sha: str = "46fbe35fd4374a00fee7de77dfddaeb6dd6a2c59"
        huggingface_hub.model_info = lambda *a, **kw: _MockInfo()
        huggingface_hub.repo_info = lambda *a, **kw: _MockInfo()

        _fastembed_available = True
        logger.info("fastembed imported and patches applied")
        return True
    except Exception as e:
        logger.warning(f"fastembed not available ({type(e).__name__}: {e}), using hash fallback for embeddings")
        return False


class RAGService:
    """RAG service with pluggable embedding backends and FAISS retrieval."""

    EMBEDDING_PROVIDERS = ("fastembed", "openai", "hash")

    def __init__(self, embedding_dim: int = 768, embedding_provider: str = "auto"):
        self.embedding_dim = embedding_dim
        self.index = None
        self.chunks = []
        self._initialized = False
        self._embed_provider = None
        self._requested_provider = embedding_provider
        self._fastembed_attempted = False
        self._faiss_attempted = False

        self._resolve_provider(embedding_provider, lazy=True)
        logger.info(
            f"RAGService initialized (dim={self.embedding_dim}, provider={self._embed_provider})"
        )

    def _resolve_provider(self, provider: str, lazy: bool = False) -> None:
        if provider == "auto":
            if _try_import_fastembed():
                self._embed_provider = "fastembed_lazy"
                if not lazy:
                    self._ensure_fastembed_loaded()
            else:
                self._embed_provider = "hash"
                self.embedding_dim = 256
        elif provider == "fastembed":
            self._embed_provider = "fastembed_lazy"
            if not lazy:
                self._ensure_fastembed_loaded()
        elif provider == "openai":
            self._embed_provider = "openai"
            self.embedding_dim = 1536
        else:
            self._embed_provider = "hash"
            self.embedding_dim = 256

    def _ensure_fastembed_loaded(self) -> bool:
        global _fastembed_model
        if self._fastembed_attempted:
            return self._embed_provider == "fastembed"
        self._fastembed_attempted = True
        if _fastembed_model is not None:
            self._embed_provider = "fastembed"
            self.embedding_dim = _fastembed_model.embedding_size
            return True
        if not _try_import_fastembed():
            self._embed_provider = "hash"
            self.embedding_dim = 256
            return False
        try:
            from fastembed import TextEmbedding
            model_name = "BAAI/bge-small-zh-v1.5"
            cache_dir = os.path.join(
                Path(__file__).resolve().parent.parent.parent, ".cache", "fastembed"
            )
            _fastembed_model = TextEmbedding(
                model_name=model_name, cache_dir=cache_dir
            )
            self._embed_provider = "fastembed"
            self.embedding_dim = _fastembed_model.embedding_size
            logger.info(f"Loaded fastembed model: {model_name} (dim={_fastembed_model.embedding_size})")
            return True
        except Exception as e:
            logger.warning(f"Failed to load fastembed: {e}, falling back to hash")
            self._embed_provider = "hash"
            self.embedding_dim = 256
            return False

    def _ensure_faiss_initialized(self) -> bool:
        if self._faiss_attempted:
            return self._initialized
        self._faiss_attempted = True
        if not _try_init_faiss():
            return False
        self.index = _faiss.IndexFlatL2(self.embedding_dim)
        self._initialized = True
        logger.info("FAISS index created")
        return True

    @property
    def is_ready(self) -> bool:
        return self._initialized and self.index is not None and self.index.ntotal > 0

    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
        if not text:
            return []
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            if chunk.strip():
                chunks.append(chunk.strip())
            start += chunk_size - overlap
        return chunks

    def _embed(self, text: str) -> list[float]:
        if self._embed_provider == "fastembed_lazy":
            self._ensure_fastembed_loaded()
        if self._embed_provider == "fastembed" and _fastembed_model is not None:
            return list(_fastembed_model.embed(text))[0].tolist()
        elif self._embed_provider == "openai":
            return self._embed_openai(text)
        else:
            return self._embed_hash(text)

    def _embed_hash(self, text: str) -> list[float]:
        h = hashlib.sha256(text.encode()).digest()
        dim = self.embedding_dim
        vec = []
        idx = 0
        while len(vec) < dim:
            h = hashlib.sha256(h + idx.to_bytes(4, "little")).digest()
            for j in range(0, len(h), 4):
                if len(vec) < dim:
                    val = int.from_bytes(h[j:j + 4], "little", signed=True) / (2 ** 31)
                    vec.append(val)
            idx += 1
        magnitude = sum(x * x for x in vec) ** 0.5
        if magnitude > 0:
            vec = [x / magnitude for x in vec]
        return vec

    def _embed_openai(self, text: str) -> list[float]:
        try:
            import httpx
            import os
            api_key = os.environ.get("OPENAI_API_KEY", "")
            base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
            if not api_key:
                return self._embed_hash(text)
            resp = httpx.post(
                f"{base_url}/embeddings",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"model": "text-embedding-3-small", "input": text},
                timeout=10.0,
            )
            if resp.status_code == 200:
                data = resp.json()
                return data["data"][0]["embedding"]
        except Exception as e:
            logger.warning(f"OpenAI embedding failed, falling back to hash: {e}")
        return self._embed_hash(text)

    def index_text(self, text: str, source_id: str = "", chunk_size: int = 500, overlap: int = 100) -> int:
        if not self._ensure_faiss_initialized():
            return 0

        chunks = self.chunk_text(text, chunk_size, overlap)
        if not chunks:
            return 0

        all_vecs = []
        for i, chunk in enumerate(chunks):
            try:
                embedding = self._embed(chunk)
                vec_np = np.array([embedding], dtype=np.float32)
                all_vecs.append(vec_np)
            except Exception as e:
                logger.warning(f"Embedding failed for chunk {i}: {e}")
                vec_np = np.array([self._embed_hash(chunk)], dtype=np.float32)
                all_vecs.append(vec_np)

            self.chunks.append({
                "text": chunk,
                "source_id": source_id,
                "chunk_index": i,
            })

        if all_vecs:
            stacked = np.vstack(all_vecs)
            self.index.add(stacked)

        logger.info(f"Indexed {len(chunks)} chunks from source '{source_id}' (provider={self._embed_provider})")
        return len(chunks)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        if not self.is_ready:
            return []

        try:
            query_vec = np.array([self._embed(query)], dtype=np.float32)
        except Exception:
            query_vec = np.array([self._embed_hash(query)], dtype=np.float32)

        k = min(top_k, self.index.ntotal)
        if k == 0:
            return []

        distances, indices = self.index.search(query_vec, k)
        results = []
        for i in range(len(indices[0])):
            idx = indices[0][i]
            if idx < 0 or idx >= len(self.chunks):
                continue
            dist = distances[0][i]
            chunk_data = self.chunks[idx]
            results.append({
                "text": chunk_data["text"],
                "source_id": chunk_data["source_id"],
                "chunk_index": chunk_data["chunk_index"],
                "score": 1.0 / (1.0 + float(dist)),
            })
        return results

    def get_context(self, query: str, max_tokens: int = 2000, top_k: int = 5) -> str:
        results = self.search(query, top_k)
        if not results:
            return ""

        context_parts = []
        total_len = 0
        for r in results:
            text = r["text"]
            if total_len + len(text) > max_tokens * 2:
                break
            context_parts.append(text)
            total_len += len(text)

        return "\n\n".join(context_parts)

    def clear(self):
        if self._initialized and _faiss_available:
            self.index = _faiss.IndexFlatL2(self.embedding_dim)
        self.chunks = []

    def save_index(self, path: str) -> bool:
        if not self._initialized or self.index is None or not _faiss_available:
            logger.warning("Cannot save: FAISS index not initialized")
            return False

        index_path = os.path.join(path, "faiss.index")
        chunks_path = os.path.join(path, "chunks.json")
        meta_path = os.path.join(path, "meta.json")

        try:
            os.makedirs(path, exist_ok=True)
            _faiss.write_index(self.index, index_path)

            import json
            with open(chunks_path, "w", encoding="utf-8") as f:
                json.dump(self.chunks, f, ensure_ascii=False)
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump({
                    "embedding_dim": self.embedding_dim,
                    "provider": self._embed_provider,
                    "chunk_count": len(self.chunks),
                    "index_size": self.index.ntotal,
                }, f, ensure_ascii=False)

            logger.info(f"FAISS index saved to {path} ({self.index.ntotal} vectors, {len(self.chunks)} chunks)")
            return True
        except Exception as e:
            logger.error(f"Failed to save FAISS index: {e}")
            return False

    def load_index(self, path: str) -> bool:
        if not _try_init_faiss():
            logger.warning("Cannot load: FAISS not available")
            return False

        import json

        index_path = os.path.join(path, "faiss.index")
        chunks_path = os.path.join(path, "chunks.json")
        meta_path = os.path.join(path, "meta.json")

        if not os.path.exists(index_path) or not os.path.exists(chunks_path):
            logger.warning(f"Index files not found in {path}")
            return False

        try:
            self.index = _faiss.read_index(index_path)

            with open(chunks_path, "r", encoding="utf-8") as f:
                self.chunks = json.load(f)

            if os.path.exists(meta_path):
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                if meta.get("embedding_dim") != self.embedding_dim:
                    logger.warning(
                        f"Index dim ({meta.get('embedding_dim')}) != service dim ({self.embedding_dim}), re-indexing recommended"
                    )

            self._initialized = True
            logger.info(f"FAISS index loaded from {path} ({self.index.ntotal} vectors, {len(self.chunks)} chunks)")
            return True
        except Exception as e:
            logger.error(f"Failed to load FAISS index: {e}")
            self.index = None
            self.chunks = []
            return False


_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service