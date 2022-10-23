from dataclasses import dataclass
from typing import List, Tuple
from itertools import permutations

@dataclass
class TestUserInfo:
    username: str
    email: str
    password: str

test_user_infos: List[TestUserInfo] = [
    TestUserInfo("testing", "abc@hello.com", "qwqjdkjwlqrqo"),
    TestUserInfo("1234", "bcd@yahoo.com", "1234567890"),
    TestUserInfo("_!@SDKJ", "321@bye.com", "asdfghjkl")
]

permuted_test_user_infos: List[Tuple[TestUserInfo, TestUserInfo]] = (
    list(permutations(test_user_infos, 2))
)
