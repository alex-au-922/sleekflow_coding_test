import time
from typing import Tuple
from fastapi import status
from fastapi.testclient import TestClient
import jwt # type: ignore
from config.auth_tokens_config import AUTH_TOKENS_CONFIG
from data_models import DatabaseConnection
from data_models.models import Account, WorkSpaceAccountLink

class TestUserInfo:
    username: str
    email: str
    password: str

class TestWorkspaceInfo:
    workspace_default_name: str
    workspace_alias: str

def create_token(username: str, exp_time: int) -> str:
    """Return an expired token"""
    
    return jwt.encode({"username": username, "exp": time.time() + exp_time}, AUTH_TOKENS_CONFIG.secret_key, algorithm=AUTH_TOKENS_CONFIG.algorithm)

class TestUserGetAllWorkspace():
    """Test for a user can get all workspace."""
   
    def test_new_user_get_empty_workspace(self, client: TestClient, login_user: Tuple[TestUserInfo, str]) -> None:
        """Test that a user can get no workspace as he or she hasn't joined any."""

        user1, access_token1 = login_user

        response = client.get(
            f"/api/user/workspace/?username={user1.username}",
            headers={"Authorization": f"Bearer {access_token1}"}
        )

        assert response.status_code == status.HTTP_200_OK
        response_json = response.json()
        assert response_json["error"] is None
        assert response_json["error_msg"] is None
        assert response_json["data"] == []
        assert response_json["msg"] == f'Get all workspaces joined by "{user1.username}" successfully.'

        with DatabaseConnection() as db:
            query_user1: Account = db.query(Account).filter(Account.username == user1.username).one()
            assert query_user1.workspaces == []
    
    def test_user_get_created_workspace(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo) -> None:
        """Test that a user can get his or her created workspace."""

        user1, access_token1 = login_user

        client.post(
            "/api/workspace/",
            json = {
                "username": user1.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
            },
            headers={"Authorization": f"Bearer {access_token1}"}
        )

        response = client.get(
            f"/api/user/workspace/?username={user1.username}",
            headers={"Authorization": f"Bearer {access_token1}"}
        )

        mock_api_result = [{
            "workspace_default_name": test_workspace_info.workspace_default_name,
            "workspace_alias": None,
        }]

        assert response.status_code == status.HTTP_200_OK
        response_json = response.json()
        assert response_json["error"] is None
        assert response_json["error_msg"] is None
        assert response_json["data"] == mock_api_result
        assert response_json["msg"] == f'Get all workspaces joined by "{user1.username}" successfully.'
    
    def test_user_get_created_workspace_with_alias(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo) -> None:
        """Test that a user can get his or her created workspace with alias."""

        user1, access_token1 = login_user

        client.post(
            "/api/workspace/",
            json = {
                "username": user1.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
            },
            headers={"Authorization": f"Bearer {access_token1}"}
        )

        response = client.put(
            "/api/workspace/alias/",
            json = {
                "username": user1.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "new_workspace_alias": test_workspace_info.workspace_alias,
            },
            headers={"Authorization": f"Bearer {access_token1}"}
        )

        response = client.get(
            f"/api/user/workspace/?username={user1.username}",
            headers={"Authorization": f"Bearer {access_token1}"}
        )

        mock_api_result = [{
            "workspace_default_name": test_workspace_info.workspace_default_name,
            "workspace_alias": test_workspace_info.workspace_alias
        }]

        assert response.status_code == status.HTTP_200_OK
        response_json = response.json()
        assert response_json["error"] is None
        assert response_json["error_msg"] is None
        assert response_json["data"] == mock_api_result
        assert response_json["msg"] == f'Get all workspaces joined by "{user1.username}" successfully.'
    
    def test_user_get_created_and_joined_workspaces(self, client: TestClient, login_users: Tuple[Tuple[TestUserInfo, str], Tuple[TestUserInfo, str]], permuted_test_workspace_info: Tuple[TestWorkspaceInfo, TestWorkspaceInfo]) -> None:
        """Test that a user can be invited to a workspace."""

        test_workspace_info1, test_workspace_info2 = permuted_test_workspace_info

        user1, access_token1 = login_users[0]
        user2, access_token2 = login_users[1]

        client.post(
            "/api/workspace/",
            json = {
                "username": user1.username,
                "workspace_default_name": test_workspace_info1.workspace_default_name,
            },
            headers={"Authorization": f"Bearer {access_token1}"}
        )

        client.put(
            f"/api/workspace/invite/",
            json = {
                "owner_username": user1.username,
                "workspace_default_name": test_workspace_info1.workspace_default_name,
                "invitee_username": user2.username
            },
            headers={"Authorization": f"Bearer {access_token1}"}
        )

        client.post(
            "/api/workspace/",
            json = {
                "username": user2.username,
                "workspace_default_name": test_workspace_info2.workspace_default_name,
            },
            headers={"Authorization": f"Bearer {access_token2}"}
        )

        response = client.get(
            f"/api/user/workspace/?username={user2.username}",
            headers={"Authorization": f"Bearer {access_token2}"}
        )

        mock_api_result = [
            {
                "workspace_default_name": test_workspace_info1.workspace_default_name,
                "workspace_alias": None,
            },
            {
                "workspace_default_name": test_workspace_info2.workspace_default_name,
                "workspace_alias": None,
            }
        ]

        assert response.status_code == status.HTTP_200_OK
        response_json = response.json()
        assert response_json["error"] is None
        assert response_json["error_msg"] is None
        assert response_json["data"] == mock_api_result
        assert response_json["msg"] == f'Get all workspaces joined by "{user2.username}" successfully.'

class TestUsersGetAllWorkspaceTokenError:
    """Test user leave workspace with token error"""

    def test_user_leave_workspace_no_access_token_raises(self, client: TestClient, login_user: Tuple[TestUserInfo, str]) -> None:
        """Test that a workspace cannot be created without access token."""

        user1, _ = login_user

        response = client.get(
            f"/api/user/workspace/?username={user1.username}",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        response_json = response.json()
        assert response_json["error"] == "UnauthorizedError"
        assert response_json["error_msg"] == "Unauthorized action."
        assert response_json["data"] is None
        assert response_json["msg"] is None
    
    def test_user_leave_workspace_wrong_access_token_raises(self, client: TestClient, login_user: Tuple[TestUserInfo, str]) -> None:
        """Test that if the access token is wrong, an error will be raised."""

        user1, access_token1 = login_user

        response = client.get(
            f"/api/user/workspace/?username={user1.username}",
            headers={"Authorization": f"Bearer {access_token1}1"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        response_json = response.json()
        assert response_json["error"] == "InvalidTokenError"
        assert response_json["error_msg"] == "Invalid token."
        assert response_json["data"] is None
        assert response_json["msg"] is None
    
    def test_user_leave_workspace_expired_access_token_raises(self, client: TestClient, login_user: Tuple[TestUserInfo, str]) -> None:
        """Test that if the access token has expired, an error will be raised."""

        user1, _ = login_user

        expired_access_token = create_token(user1.username, -1)

        response = client.get(
            f"/api/user/workspace/?username={user1.username}",
            headers={"Authorization": f"Bearer {expired_access_token}"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        response_json = response.json()
        assert response_json["error"] == "TokenExpiredError"
        assert response_json["error_msg"] == "Token has expired."
        assert response_json["data"] is None
        assert response_json["msg"] is None

class TestUserGetAllWorkspaceInputError:
    """Test the get all workspace api with input error."""

    def test_get_all_workspace_user_not_exists_raises(self, client: TestClient, test_user_info: TestUserInfo) -> None:
        """Test that if the user of the workspace does not exist, an error will be raised."""

        leaky_access_token = create_token(test_user_info.username, 100)

        response = client.get(
            f"/api/user/workspace/?username={test_user_info.username}",
            headers={"Authorization": f"Bearer {leaky_access_token}"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_json = response.json()
        assert response_json["error"] == "NotFoundError"
        assert response_json["error_msg"] == f'User "{test_user_info.username}" not found.'
        assert response_json["msg"] is None
        assert response_json["data"] is None