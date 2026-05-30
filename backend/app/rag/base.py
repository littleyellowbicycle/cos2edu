from abc import ABC, abstractmethod
from typing import List, Dict


class BaseRAGProvider(ABC):
    @abstractmethod
    async def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        pass

    @abstractmethod
    async def add_documents(self, documents: List[Dict]) -> bool:
        pass

    @abstractmethod
    async def delete_documents(self, doc_ids: List[str]) -> bool:
        pass

    @property
    @abstractmethod
    def is_ready(self) -> bool:
        pass