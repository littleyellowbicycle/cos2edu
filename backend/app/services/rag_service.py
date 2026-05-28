import hashlib
import json
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


class RAGService:
    """Minimal RAG service using FAISS for vector retrieval."""

    def __init__(self, embedding_dim: int = 768):
        self.embedding_dim = embedding_dim
        self.index = None
        self.chunks = []
        self._initialized = False

        if _faiss_available:
            self.index = faiss.IndexFlatL2(embedding_dim)
            self._initialized = True
            logger.info(f"RAGService initialized with FAISS (dim={embedding_dim})")
        else:
            logger.info("RAGService initialized in long-context fallback mode (no FAISS)")

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

    def _simple_embed(self, text: str) -> list[float]:
        """Simple hash-based pseudo-embedding for MVP. Should be replaced with real embeddings."""
        h = hashlib.sha256(text.encode()).digest()
        dim = self.embedding_dim
        vec = []
        for i in range(dim):
            byte_idx = (i * 4) % len(h)
            val = int.from_bytes(h[byte_idx:byte_idx + 4 % len(h)], 'little', signed=True) / (2 ** 31)
            vec.append(val)
        magnitude = sum(x * x for x in vec) ** 0.5
        if magnitude > 0:
            vec = [x / magnitude for x in vec]
        return vec

    def index_text(self, text: str, source_id: str = "", chunk_size: int = 500, overlap: int = 100) -> int:
        if not self._initialized or not _faiss_available:
            return 0

        chunks = self.chunk_text(text, chunk_size, overlap)
        vectors = []
        for i, chunk in enumerate(chunks):
            embedding = self._simple_embed(chunk)
            vec_np = np.array([embedding], dtype=np.float32)
            vectors.append(vec_np)
            self.chunks.append({
                "text": chunk,
                "source_id": source_id,
                "chunk_index": i,
            })

        if vectors:
            all_vecs = np.vstack(vectors)
            self.index.add(all_vecs)

        logger.info(f"Indexed {len(chunks)} chunks from source '{source_id}'")
        return len(chunks)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        if not self.is_ready:
            return []

        query_vec = np.array([self._simple_embed(query)], dtype=np.float32)
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