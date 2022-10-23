from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional
from sqlalchemy.orm import Query # type: ignore

class FilterHandler(ABC):

    @abstractmethod
    def register_filter(self, query: Query, field: str, filter_str: Optional[str] = None) -> FilterHandler:
        """Register filter to handler"""


    @abstractmethod
    def get_filter_query(self) -> Query:
        """Get filtered query"""