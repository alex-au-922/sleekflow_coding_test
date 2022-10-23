from dataclasses import dataclass
from typing import List, Tuple
from itertools import permutations

@dataclass
class TestTodoListInfo:
    todolist_name: str

test_todolist_infos: List[TestTodoListInfo] = [
    TestTodoListInfo("todolist_testing"),
    TestTodoListInfo("1234"),
    TestTodoListInfo("hello_world!"),
]

permuted_test_todolist_infos: List[Tuple[TestTodoListInfo, TestTodoListInfo]] = (
    list(permutations(test_todolist_infos, 2))
)
