from typing import Literal, TypeAlias
from .interface import FilterHandler
from .todo_query_filter_handler import TodoQueryFilterHandler

HandlerType: TypeAlias = Literal["Todo"]

class FilterHandlerFactory:

    def get_handler(self, handler_type: HandlerType) -> FilterHandler:
        match handler_type:
            case "Todo":
                return TodoQueryFilterHandler()
            case _:
                raise NotImplementedError(f"Handler type {handler_type} is not implemented")