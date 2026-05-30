import pytest
from app.rag.simple_rag import SimpleRAGProvider


class TestSimpleRAGProviderInit:

    def test_init_without_faiss(self):
        provider = SimpleRAGProvider(embedding_dim=384, use_sentence_transformers=False)
        assert provider.embedding_dim == 384
        assert provider.is_ready is False

    def test_init_with_faiss(self):
        try:
            import faiss
            provider = SimpleRAGProvider(embedding_dim=384, use_sentence_transformers=False)
            assert provider._initialized is True
            assert provider.is_ready is False
        except ImportError:
            pass


class TestSimpleRAGProviderChunkText:

    def setup_method(self):
        self.provider = SimpleRAGProvider(embedding_dim=384, use_sentence_transformers=False)

    def test_chunk_text_empty(self):
        assert self.provider.chunk_text("") == []

    def test_chunk_text_short(self):
        text = "Short text"
        chunks = self.provider.chunk_text(text)
        assert len(chunks) >= 1
        assert chunks[0].strip() == "Short text"

    def test_chunk_text_long(self):
        text = "A" * 2000
        chunks = self.provider.chunk_text(text, chunk_size=500, overlap=100)
        assert len(chunks) > 1

    def test_chunk_text_overlap(self):
        text = "Word " * 200
        chunks = self.provider.chunk_text(text, chunk_size=100, overlap=20)
        assert len(chunks) > 1


class TestSimpleRAGProviderHashEmbedding:

    def setup_method(self):
        self.provider = SimpleRAGProvider(embedding_dim=384, use_sentence_transformers=False)

    def test_hash_embed_returns_correct_dim(self):
        vec = self.provider._hash_embed("test text")
        assert len(vec) == 384

    def test_hash_embed_normalized(self):
        vec = self.provider._hash_embed("test text")
        magnitude = sum(x * x for x in vec) ** 0.5
        assert abs(magnitude - 1.0) < 0.01

    def test_hash_embed_deterministic(self):
        vec1 = self.provider._hash_embed("test text")
        vec2 = self.provider._hash_embed("test text")
        assert vec1 == vec2

    def test_hash_embed_different_texts(self):
        vec1 = self.provider._hash_embed("hello")
        vec2 = self.provider._hash_embed("world")
        assert vec1 != vec2


class TestSimpleRAGProviderIndexAndSearch:

    def setup_method(self):
        try:
            import faiss
        except ImportError:
            pytest.skip("faiss not available")
        self.provider = SimpleRAGProvider(embedding_dim=384, use_sentence_transformers=False)
        self.text = "Python is a programming language. Python emphasizes code readability. Python supports multiple programming paradigms."

    def test_index_text(self):
        count = self.provider.index_text(self.text, source_id="test_doc")
        assert count > 0
        assert self.provider.is_ready is True

    def test_search_returns_results(self):
        self.provider.index_text(self.text, source_id="test_doc")
        results = self.provider.search("programming language", top_k=3)
        assert len(results) > 0
        assert "text" in results[0]

    def test_search_empty_index(self):
        results = self.provider.search("test", top_k=3)
        assert results == []

    def test_get_context(self):
        self.provider.index_text(self.text, source_id="test_doc")
        context = self.provider.get_context("Python programming", max_tokens=500)
        assert isinstance(context, str)
        assert len(context) > 0

    def test_clear(self):
        self.provider.index_text(self.text, source_id="test_doc")
        assert self.provider.is_ready is True
        self.provider.clear()
        assert self.provider.is_ready is False