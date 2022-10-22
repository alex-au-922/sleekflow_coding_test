import pytest
from fastapi.testclient import TestClient
from typing import Protocol, Tuple
from dataclasses import dataclass

class TestUserInfo:
    username: str
    email: str
    password: str

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
