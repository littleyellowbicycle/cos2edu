from app.rag.base import BaseRAGProvider
from app.rag.simple_rag import SimpleRAGProvider


def get_rag_provider(provider: str = None) -> BaseRAGProvider:
    if provider is None:
        from app.core.config import settings
        provider = getattr(settings, "RAG_PROVIDER", "simple")

    if provider == "simple":
        return SimpleRAGProvider()
    raise ValueError(f"Unknown RAG provider: {provider}")


__all__ = ["BaseRAGProvider", "SimpleRAGProvider", "get_rag_provider"]