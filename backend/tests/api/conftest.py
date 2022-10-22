from typing import Generator, List, Tuple
import pytest
from pytest import FixtureRequest
from fastapi.testclient import TestClient
from util.helper.string import StringHash, StringHashFactory
from ...main import app
from data_models import Base, Engine
from itertools import permutations
from dataclasses import dataclass

@pytest.fixture
def hasher() -> StringHash:
    """Return a StringHash object"""
    
    return StringHashFactory().get_hasher("blake2b")

@pytest.fixture
def db_teardown_and_setup() -> Generator[None, None, None]:
    Base.metadata.drop_all(bind = Engine)
    Base.metadata.create_all(bind = Engine)
    yield
    Base.metadata.drop_all(bind = Engine)

@pytest.fixture
def client(db_teardown_and_setup) -> Generator[TestClient, None, None]:
    with TestClient(app) as client:
        yield client
@dataclass
class TestUserInfo:
    username: str
    email: str
    password: str

test_user_infos: List[TestUserInfo] = [
    TestUserInfo("testing", "abc@hello.com", "qwqjdkjwlqrqo"),
    TestUserInfo("1234", "bcd@yahoo.com", "1234567890"),
    TestUserInfo("hello_world!", "testing@gmail.com", "qwertyuiop"),
    TestUserInfo("!@#!@#*%(*&$(*", "321@bye.com", "asdfghjkl")
]

permuted_test_user_infos: List[Tuple[TestUserInfo, TestUserInfo]] = list(permutations(test_user_infos, 2))

@pytest.fixture(params = test_user_infos)
def test_user_info(request: FixtureRequest) -> TestUserInfo:
    """Return a TestUserInfo object"""
    
    return request.param

@pytest.fixture(params = permuted_test_user_infos)
def permuted_test_user_info(request: FixtureRequest) -> Tuple[TestUserInfo, TestUserInfo]:
    """Return a tuple of two TestUserInfo objects"""
    
    return request.param
