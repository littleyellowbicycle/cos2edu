import hashlib
from typing import Optional
from pathlib import Path

from app.core.logging_config import get_logger

logger = get_logger(__name__)

_faiss_available = False
try:
    import faiss
    import numpy as np
    _faiss_available = True
except ImportError:
    logger.warning("faiss or numpy not available, RAG will use long-context fallback")

_sentence_transformers_available = False
_sentence_model = None
try:
    from sentence_transformers import SentenceTransformer
    _sentence_transformers_available = True
except ImportError:
    pass


class RAGService:
    """RAG service with pluggable embedding backends and FAISS retrieval."""

    EMBEDDING_PROVIDERS = ("sentence_transformer", "openai", "hash")

    def __init__(self, embedding_dim: int = 768, embedding_provider: str = "auto"):
        self.embedding_dim = embedding_dim
        self.index = None
        self.chunks = []
        self._initialized = False
        self._embed_provider = None

        if not _faiss_available:
            logger.info("RAGService initialized in long-context fallback mode (no FAISS)")
            return

        self._resolve_provider(embedding_provider)
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        self._initialized = True
        logger.info(
            f"RAGService initialized (dim={self.embedding_dim}, provider={self._embed_provider})"
        )

    def _resolve_provider(self, provider: str) -> None:
        if provider == "auto":
            if _sentence_transformers_available:
                self._init_sentence_transformer()
            else:
                self._embed_provider = "hash"
                self.embedding_dim = 256
        elif provider == "sentence_transformer":
            self._init_sentence_transformer()
        elif provider == "openai":
            self._embed_provider = "openai"
            self.embedding_dim = 1536
        else:
            self._embed_provider = "hash"
            self.embedding_dim = 256

    def _init_sentence_transformer(self) -> None:
        global _sentence_model
        try:
            if _sentence_model is None:
                model_name = "all-MiniLM-L6-v2"
                _sentence_model = SentenceTransformer(model_name)
                logger.info(f"Loaded sentence-transformers model: {model_name}")
            self._embed_provider = "sentence_transformer"
            self.embedding_dim = _sentence_model.get_sentence_embedding_dimension()
        except Exception as e:
            logger.warning(f"Failed to load sentence-transformers: {e}, falling back to hash")
            self._embed_provider = "hash"
            self.embedding_dim = 256

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
        if self._embed_provider == "sentence_transformer" and _sentence_model is not None:
            return _sentence_model.encode(text).tolist()
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
        if not self._initialized or not _faiss_available:
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
            self.index = faiss.IndexFlatL2(self.embedding_dim)
        self.chunks = []


_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service