from .interface import FilterHandler, Query
from sqlalchemy.orm import Query # type: ignore
from typing import Optional
from .filter_pattern_match import FilterPatternMatch
from ..models import Todo

class TodoQueryFilterHandler(FilterHandler):
    def __init__(self) -> None:
        self.__query: Optional[Query] = None
        self.__field: Optional[str] = None
        self.__filter_str: Optional[str] = None

    def register_filter(self, query: Query, field: str, filter_str: Optional[str] = None) -> FilterHandler:
        self.__query = query
        self.__field = field
        self.__filter_str = filter_str
        return self
    
    def __parse_null(self, value: str) -> Optional[str]:
        if value.lower() == "null":
            return None
        return value

    def get_filter_query(self) -> Query:
        if self.__query is None:
            raise ValueError("Query is not registered")
        if self.__field is None:
            raise ValueError("Field is not registered")
        if self.__filter_str is None:
            raise ValueError("Filter is not registered")

        filter_pattern_match = FilterPatternMatch(self.__filter_str)
        filter_pattern_match()

        operator = filter_pattern_match.get_operator()
        value = self.__parse_null(filter_pattern_match.get_value())
        match operator:
            case "eq":
                return self.__query.filter(getattr(Todo, self.__field) == value)
            case "gt":
                return self.__query.filter(getattr(Todo, self.__field) > value)
            case "lt":
                return self.__query.filter(getattr(Todo, self.__field) < value)
            case "ge":
                return self.__query.filter(getattr(Todo, self.__field) >= value)
            case "le":
                return self.__query.filter(getattr(Todo, self.__field) <= value)
            case "ne":
                return self.__query.filter(getattr(Todo, self.__field) != value)
            case _:
                raise ValueError("Invalid operator")