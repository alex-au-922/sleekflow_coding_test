import time
from typing import Tuple
from fastapi import status
from fastapi.testclient import TestClient
import jwt # type: ignore
from config.auth_tokens_config import AUTH_TOKENS_CONFIG
from data_models import DatabaseConnection
from data_models.models import Account, WorkSpace, WorkSpaceAccountLink
from typing import Protocol, Tuple
from dataclasses import dataclass

class TestUserInfo:
    username: str
    email: str
    password: str

def create_token(username: str, exp_time: int) -> str:
    """Return an expired token"""
    
    return jwt.encode({"username": username, "exp": time.time() + exp_time}, AUTH_TOKENS_CONFIG.secret_key, algorithm=AUTH_TOKENS_CONFIG.algorithm)

class TestCreateWorkSpace:
    """Test the create workspace."""

    def test_create_workspace(self, client: TestClient, login_user: Tuple[TestUserInfo, str]) -> None:
        """Test that a workspace can be created."""
        user, access_token = login_user

        response = client.post(
            "/api/workspace/",
            json = {
                "username": user.username,
                "workspace_default_name": "workspace_testing",
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == status.HTTP_201_CREATED
        response_json = response.json()
        assert response_json["error"] is None
        assert response_json["error_msg"] is None
        assert isinstance(response_json["data"], int)
        assert response_json["msg"] == 'Workspace "workspace_testing" created successfully.'

        with DatabaseConnection() as db:
            workspace: WorkSpace = db.query(WorkSpace).filter(WorkSpace.workspace_default_name == "workspace_testing").one()
            assert workspace.workspace_id == int(response_json["data"])
    
    def test_create_workspace_creator_joined(self, client: TestClient, login_user: Tuple[TestUserInfo, str]) -> None:
        """Test that for the creator who created the workspace, he or she is also joined the workspace."""
        user, access_token = login_user

        response = client.post(
            "/api/workspace/",
            json = {
                "username": user.username,
                "workspace_default_name": "workspace_testing",
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == status.HTTP_201_CREATED
        response_json = response.json()
        assert response_json["error"] is None
        assert response_json["error_msg"] is None
        assert isinstance(response_json["data"], int)
        assert response_json["msg"] == 'Workspace "workspace_testing" created successfully.'

        with DatabaseConnection() as db:
            workspace_account_link: WorkSpaceAccountLink = db.query(WorkSpaceAccountLink).filter(WorkSpaceAccountLink.workspace_id == int(response_json["data"])).first()
            query_user: Account = db.query(Account).filter(Account.user_id == workspace_account_link.user_id).one()
            assert user.username == query_user.username

class TestCreateWorkSpaceTokenError:
    """Test the create workspace with token error."""

    def test_create_workspace_no_access_token_raises(self, client: TestClient, login_user: Tuple[TestUserInfo, str]) -> None:
        """Test that a workspace cannot be created without access token."""
        
        user, _ = login_user
        response = client.post(
            "/api/workspace/",
            json = {
                "username": user.username,
                "workspace_default_name": "workspace_testing",
            },
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        response_json = response.json()
        assert response_json["error"] == "UnauthorizedError"
        assert response_json["error_msg"] == "Unauthorized action."
        assert response_json["data"] is None
        assert response_json["msg"] is None
    
    def test_create_workspace_wrong_access_token_raises(self, client: TestClient, login_user: Tuple[TestUserInfo, str]) -> None:
        """Test that if the access token is wrong, an error will be raised."""
        user, access_token = login_user

        response = client.post(
            "/api/workspace/",
            json = {
                "username": user.username,
                "workspace_default_name": "workspace_testing",
            },
            headers={"Authorization": f"Bearer {access_token}1"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        response_json = response.json()
        assert response_json["error"] == "InvalidTokenError"
        assert response_json["error_msg"] == "Invalid token."
        assert response_json["data"] is None
        assert response_json["msg"] is None
    
    def test_create_workspace_expired_access_token_raises(self, client: TestClient, login_user: Tuple[TestUserInfo, str]) -> None:
        """Test that if the access token has expired, an error will be raised."""

        user, _ = login_user

        expired_access_token = create_token("testing", -1)

        response = client.post(
            "/api/workspace/",
            json = {
                "username": user.username,
                "workspace_default_name": "workspace_testing",
            },
            headers={"Authorization": f"Bearer {expired_access_token}"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        response_json = response.json()
        assert response_json["error"] == "TokenExpiredError"
        assert response_json["error_msg"] == "Token has expired."
        assert response_json["data"] is None
        assert response_json["msg"] is None

class TestCreateWorkSpaceInputError:
    """Test the create workspace with input error."""

    def test_create_workspace_creator_not_exists_raises(self, client: TestClient) -> None:
        """Test that if the creator of the workspace does not exist, an error will be raised."""

        leaky_access_token = create_token("testing", 100)

        response = client.post(
            "/api/workspace/",
            json = {
                "username": "testing",
                "workspace_default_name": "workspace_testing",
            },
            headers={"Authorization": f"Bearer {leaky_access_token}"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_json = response.json()
        assert response_json["error"] == "NotFoundError"
        assert response_json["error_msg"] == f'User "testing" not found.'
        assert response_json["msg"] is None
        assert response_json["data"] is None

    def test_create_workspace_same_default_name_raises(self, client: TestClient, login_user: Tuple[TestUserInfo, str]) -> None:
        """Test that if the workspace with the same default name exists, an error will be raised."""

        user, access_token = login_user

        client.post(
            "/api/workspace/",
            json = {
                "username": user.username,
                "workspace_default_name": "workspace_testing",
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        response = client.post(
            "/api/workspace/",
            json = {
                "username": user.username,
                "workspace_default_name": "workspace_testing",
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == status.HTTP_409_CONFLICT
        response_json = response.json()
        assert response_json["error"] == "DuplicateError"
        assert response_json["error_msg"] == f'Workspace "workspace_testing" already exists.'
        assert response_json["msg"] is None
        assert response_json["data"] is None
    
    def test_create_workspace_empty_name_raises(self, client: TestClient, login_user: Tuple[TestUserInfo, str]) -> None:
        """Test that when creating a workspace of empty name, an error will be raised."""
        user, access_token = login_user

        response = client.post(
            "/api/workspace/",
            json = {
                "username": user.username,
                "workspace_default_name": "",
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        response_json = response.json()
        assert response_json["error"] == "ValidationError"
        assert 'Workspace default name cannot be empty!' in response_json["error_msg"]
        assert response_json["msg"] is None
        assert response_json["data"] is None