import hashlib
from typing import List, Dict, Optional

from app.rag.base import BaseRAGProvider
from app.core.logging_config import get_logger

logger = get_logger(__name__)

_faiss_available = False
try:
    import faiss
    import numpy as np
    _faiss_available = True
except ImportError:
    logger.warning("faiss or numpy not available, SimpleRAGProvider will use long-context fallback")

_sentence_transformers_available = False
try:
    from sentence_transformers import SentenceTransformer
    _sentence_transformers_available = True
except ImportError:
    logger.info("sentence-transformers not available, using hash-based pseudo-embeddings")


class SimpleRAGProvider(BaseRAGProvider):
    def __init__(self, embedding_dim: int = 384, use_sentence_transformers: bool = True):
        self.embedding_dim = embedding_dim
        self.index = None
        self.chunks: List[Dict] = []
        self._initialized = False
        self._model = None
        self._use_real_embeddings = False

        if _faiss_available:
            self.index = faiss.IndexFlatL2(embedding_dim)
            self._initialized = True

            if use_sentence_transformers and _sentence_transformers_available:
                try:
                    model_name = "all-MiniLM-L6-v2"
                    logger.info(f"Loading sentence-transformers model: {model_name}")
                    self._model = SentenceTransformer(model_name)
                    self._use_real_embeddings = True
                    logger.info("SimpleRAGProvider initialized with sentence-transformers embeddings")
                except Exception as e:
                    logger.warning(f"Failed to load sentence-transformers: {e}, falling back to hash embeddings")
            else:
                logger.info("SimpleRAGProvider initialized with hash-based pseudo-embeddings (no sentence-transformers)")
        else:
            logger.info("SimpleRAGProvider initialized in long-context fallback mode (no FAISS)")

    @property
    def is_ready(self) -> bool:
        return self._initialized and self.index is not None and self.index.ntotal > 0

    def _embed(self, text: str) -> List[float]:
        if self._use_real_embeddings and self._model is not None:
            try:
                embedding = self._model.encode(text, normalize_embeddings=True)
                return embedding.tolist()
            except Exception as e:
                logger.warning(f"Sentence-transformers encoding failed: {e}, falling back to hash")
                return self._hash_embed(text)
        return self._hash_embed(text)

    def _hash_embed(self, text: str) -> List[float]:
        h = hashlib.sha256(text.encode()).digest()
        dim = self.embedding_dim
        vec = []
        for i in range(dim):
            byte_idx = (i * 4) % len(h)
            if byte_idx + 4 > len(h):
                break
            val = int.from_bytes(h[byte_idx:byte_idx + 4], 'little', signed=True) / (2 ** 31)
            vec.append(val)
        magnitude = sum(x * x for x in vec) ** 0.5
        if magnitude > 0:
            vec = [x / magnitude for x in vec]
        return vec

    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
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

    async def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        if not self.is_ready:
            return []

        query_vec = self._embed(query)
        query_np = np.array([query_vec], dtype=np.float32)
        k = min(top_k, self.index.ntotal)
        if k == 0:
            return []

        distances, indices = self.index.search(query_np, k)
        results = []
        for i in range(len(indices[0])):
            idx = indices[0][i]
            if idx < 0 or idx >= len(self.chunks):
                continue
            dist = distances[0][i]
            chunk_data = self.chunks[idx]
            results.append({
                "text": chunk_data["text"],
                "source_id": chunk_data.get("source_id", ""),
                "chunk_index": chunk_data.get("chunk_index", 0),
                "score": 1.0 / (1.0 + float(dist)),
            })
        return results

    async def add_documents(self, documents: List[Dict]) -> bool:
        if not self._initialized or not _faiss_available:
            return False

        vectors = []
        for doc in documents:
            text = doc.get("content", "")
            source_id = doc.get("source_id", "")
            chunks = self.chunk_text(text, doc.get("chunk_size", 500), doc.get("overlap", 100))
            for i, chunk in enumerate(chunks):
                embedding = self._embed(chunk)
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

        logger.info(f"Indexed {len(vectors)} chunks from {len(documents)} documents")
        return True

    async def delete_documents(self, doc_ids: List[str]) -> bool:
        remaining_chunks = [c for c in self.chunks if c.get("source_id") not in doc_ids]
        if len(remaining_chunks) == len(self.chunks):
            return True

        self.chunks = remaining_chunks

        if self._initialized and _faiss_available:
            vectors = []
            for chunk in self.chunks:
                embedding = self._embed(chunk["text"])
                vec_np = np.array([embedding], dtype=np.float32)
                vectors.append(vec_np)
            self.index = faiss.IndexFlatL2(self.embedding_dim)
            if vectors:
                all_vecs = np.vstack(vectors)
                self.index.add(all_vecs)

        logger.info(f"Deleted documents {doc_ids}, re-indexed {len(self.chunks)} remaining chunks")
        return True

    def index_text(self, text: str, source_id: str = "", chunk_size: int = 500, overlap: int = 100) -> int:
        if not self._initialized or not _faiss_available:
            return 0

        chunks = self.chunk_text(text, chunk_size, overlap)
        vectors = []
        for i, chunk in enumerate(chunks):
            embedding = self._embed(chunk)
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

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        if not self.is_ready:
            return []

        query_vec = self._embed(query)
        query_np = np.array([query_vec], dtype=np.float32)
        k = min(top_k, self.index.ntotal)
        if k == 0:
            return []

        distances, indices = self.index.search(query_np, k)
        results = []
        for i in range(len(indices[0])):
            idx = indices[0][i]
            if idx < 0 or idx >= len(self.chunks):
                continue
            dist = distances[0][i]
            chunk_data = self.chunks[idx]
            results.append({
                "text": chunk_data["text"],
                "source_id": chunk_data.get("source_id", ""),
                "chunk_index": chunk_data.get("chunk_index", 0),
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