from dataclasses import dataclass
from typing import List, Tuple
from itertools import permutations

@dataclass
class TestWorkspaceInfo:
    workspace_default_name: str
    workspace_alias: str = ""

test_workspace_infos: List[TestWorkspaceInfo] = [
    TestWorkspaceInfo("workspace_testing"),
    TestWorkspaceInfo("1234", "1234"),
    TestWorkspaceInfo("hello_world!", ""),
]

permuted_test_workspace_infos: List[Tuple[TestWorkspaceInfo, TestWorkspaceInfo]] = (
    list(permutations(test_workspace_infos, 2))
)

