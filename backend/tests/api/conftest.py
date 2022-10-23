from typing import Generator, List, Tuple
import pytest
from pytest import FixtureRequest
from fastapi.testclient import TestClient
from util.helper.string import StringHash, StringHashFactory
from ...main import app
from data_models import Base, Engine
from ..mock_data import (
    TestUserInfo,
    permuted_test_user_infos,
    test_user_infos,
    TestWorkspaceInfo,
    permuted_test_workspace_infos,
    test_workspace_infos,
    TestTodoListInfo,
    permuted_test_todolist_infos,
    test_todolist_infos,
)
from util.helper.string import random_string

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

@pytest.fixture(params = test_user_infos)
def test_user_info(request: FixtureRequest) -> TestUserInfo:
    """Return a TestUserInfo object"""
    
    return request.param

@pytest.fixture(params = permuted_test_user_infos)
def permuted_test_user_info(request: FixtureRequest) -> Tuple[TestUserInfo, TestUserInfo]:
    """Return a tuple of two TestUserInfo objects"""
    
    return request.param

@pytest.fixture(params = test_workspace_infos)
def test_workspace_info(request: FixtureRequest) -> TestWorkspaceInfo:
    """Return a TestWorkspaceInfo object"""
    
    return request.param

@pytest.fixture(params = permuted_test_workspace_infos)
def permuted_test_workspace_info(request: FixtureRequest) -> Tuple[TestWorkspaceInfo, TestWorkspaceInfo]:
    """Return a tuple of two TestWorkspaceInfo objects"""
    
    return request.param


@pytest.fixture(params = test_todolist_infos)
def test_todolist_info(request: FixtureRequest) -> TestTodoListInfo:
    """Return a TestWorkspaceInfo object"""
    
    return request.param

@pytest.fixture(params = permuted_test_todolist_infos)
def permuted_test_todolist_info(request: FixtureRequest) -> Tuple[TestTodoListInfo, TestTodoListInfo]:
    """Return a tuple of two TestWorkspaceInfo objects"""
    
    return request.param

short_random_strings: List[str] = [
    random_string(5) for _ in range(5)
]

long_random_strings: List[str] = [
    random_string(10) for _ in range(5)
]

@pytest.fixture(params = short_random_strings)
def short_random_string(request: FixtureRequest) -> str:
    """Return a short random string"""
    
    return request.param

@pytest.fixture(params = long_random_strings)
def long_random_string(request: FixtureRequest) -> str:
    """Return a long random string"""
    
    return request.param

@pytest.fixture
def create_user(client: TestClient, test_user_info: TestUserInfo) -> TestUserInfo:
    """Create a user."""
    
    client.post(
        "/api/user/",
        json = {
            "username": test_user_info.username,
            "email": test_user_info.email,
            "password": test_user_info.password,
        }
    )
    return test_user_info

@pytest.fixture
def create_users(client: TestClient, permuted_test_user_info: Tuple[TestUserInfo, TestUserInfo]) -> Tuple[TestUserInfo, TestUserInfo]:
    """Create multiple users."""
    
    first_test_user_info, second_test_user_info = permuted_test_user_info

    client.post(
        "/api/user/",
        json = {
            "username": first_test_user_info.username,
            "email": first_test_user_info.email,
            "password": first_test_user_info.password,
        }
    )
    
    client.post(
        "/api/user/",
        json = {
            "username": second_test_user_info.username,
            "email": second_test_user_info.email,
            "password": second_test_user_info.password,
        }
    )

    return permuted_test_user_info

@pytest.fixture
def login_user(client: TestClient, create_user: TestUserInfo) -> Tuple[TestUserInfo, str]:
    """Login a user."""
    
    login_response = client.post(
        "/api/login/",
        json = {
            "input_field": create_user.username,
            "password": create_user.password,
        }
    )

    access_token = login_response.json()["data"]["access_token"]
    return create_user, access_token

@pytest.fixture
def login_users(client: TestClient, create_users: Tuple[TestUserInfo, TestUserInfo]) -> Tuple[Tuple[TestUserInfo, str], Tuple[TestUserInfo, str]]:
    """Login multiple users."""
    
    first_test_user_info, second_test_user_info = create_users

    first_login_response = client.post(
        "/api/login/",
        json = {
            "input_field": first_test_user_info.username,
            "password": first_test_user_info.password,
        }
    )

    first_access_token = first_login_response.json()["data"]["access_token"]

    second_login_response = client.post(
        "/api/login/",
        json = {
            "input_field": second_test_user_info.username,
            "password": second_test_user_info.password,
        }
    )

    second_access_token = second_login_response.json()["data"]["access_token"]
    return (first_test_user_info, first_access_token), (second_test_user_info, second_access_token)
