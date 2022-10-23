import time
from typing import Tuple
from fastapi import status
from fastapi.testclient import TestClient
import jwt # type: ignore
from config.auth_tokens_config import AUTH_TOKENS_CONFIG
from data_models import DatabaseConnection
from data_models.models import Account
from ...mock_data import TestUserInfo, TestWorkspaceInfo

def create_token(username: str, exp_time: int) -> str:
    """Return an expired token"""
    
    return jwt.encode({"username": username, "exp": time.time() + exp_time}, AUTH_TOKENS_CONFIG.secret_key, algorithm=AUTH_TOKENS_CONFIG.algorithm)

class TestUserLeaveWorkspace():
    """Test that a user can leave a workspace."""
   
    def test_non_owner_user_leave_workspace(self, client: TestClient, login_users: Tuple[Tuple[TestUserInfo, str], Tuple[TestUserInfo, str]], test_workspace_info: TestWorkspaceInfo) -> None:
        """Test that a user can be invited to a workspace."""

        user1, access_token1 = login_users[0]
        user2, access_token2 = login_users[1]

        client.post(
            "/api/workspace/",
            json = {
                "username": user1.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
            },
            headers={"Authorization": f"Bearer {access_token1}"}
        )

        client.put(
            "/api/workspace/invite/",
            json = {
                "owner_username": user1.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "invitee_username": user2.username,
            },
            headers={"Authorization": f"Bearer {access_token1}"}
        )

        with DatabaseConnection() as db:
            query_user2: Account = db.query(Account).filter(Account.username == user2.username).one()
            assert len(query_user2.workspaces) == 1

        response = client.delete(
            "/api/workspace/",
            json = {
                "username": user2.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
            },
            headers={"Authorization": f"Bearer {access_token2}"}
        )

        assert response.status_code == status.HTTP_202_ACCEPTED
        response_json = response.json()
        assert response_json["error"] is None
        assert response_json["error_msg"] is None
        assert response_json["data"] is None
        assert response_json["msg"] == f'User "{user2.username}" has left workspace "{test_workspace_info.workspace_default_name}" successfully.'

        with DatabaseConnection() as db:
            query_user2 = db.query(Account).filter(Account.username == user2.username).one()
            assert query_user2.workspaces == []
    
    def test_owner_user_leave_workspace(self, client: TestClient, login_users: Tuple[Tuple[TestUserInfo, str], Tuple[TestUserInfo, str]], test_workspace_info: TestWorkspaceInfo) -> None:
        """Test that a user can be invited to a workspace."""

        user1, access_token1 = login_users[0]
        user2, _ = login_users[1]

        client.post(
            "/api/workspace/",
            json = {
                "username": user1.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
            },
            headers={"Authorization": f"Bearer {access_token1}"}
        )

        client.put(
            "/api/workspace/invite/",
            json = {
                "owner_username": user1.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "invitee_username": user2.username,
            },
            headers={"Authorization": f"Bearer {access_token1}"}
        )

        with DatabaseConnection() as db:
            query_user2: Account = db.query(Account).filter(Account.username == user2.username).one()
            assert len(query_user2.workspaces) == 1

        response = client.delete(
            "/api/workspace/",
            json = {
                "username": user1.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
            },
            headers={"Authorization": f"Bearer {access_token1}"}
        )

        assert response.status_code == status.HTTP_202_ACCEPTED
        response_json = response.json()
        assert response_json["error"] is None
        assert response_json["error_msg"] is None
        assert response_json["data"] is None
        assert response_json["msg"] == f'User "{user1.username}" has left workspace "{test_workspace_info.workspace_default_name}" successfully.'

        with DatabaseConnection() as db:
            query_user1: Account = db.query(Account).filter(Account.username == user1.username).one()
            assert query_user1.workspaces == []

        with DatabaseConnection() as db:
            query_user2 = db.query(Account).filter(Account.username == user2.username).one()
            assert query_user2.workspaces == []


class TestUsersleaveWorkspaceTokenError:
    """Test user leave workspace with token error"""

    def test_user_leave_workspace_no_access_token_raises(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo) -> None:
        """Test that a workspace cannot be exited without access token."""

        user1, access_token1 = login_user

        client.post(
            "/api/workspace/",
            json = {
                "username": user1.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
            },
            headers={"Authorization": f"Bearer {access_token1}"}
        )

        response = client.delete(
            "/api/workspace/",
            json = {
                "username": user1.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
            },
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        response_json = response.json()
        assert response_json["error"] == "UnauthorizedError"
        assert response_json["error_msg"] == "Unauthorized action."
        assert response_json["data"] is None
        assert response_json["msg"] is None
    
    def test_user_leave_workspace_wrong_access_token_raises(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo) -> None:
        """Test that if the access token is wrong, an error will be raised."""

        user1, access_token1 = login_user

        client.post(
            "/api/workspace/",
            json = {
                "username": user1.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
            },
            headers={"Authorization": f"Bearer {access_token1}"}
        )

        response = client.delete(
            "/api/workspace/",
            json = {
                "username": user1.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
            },
            headers={"Authorization": f"Bearer {access_token1}1"}
        )


        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        response_json = response.json()
        assert response_json["error"] == "InvalidTokenError"
        assert response_json["error_msg"] == "Invalid token."
        assert response_json["data"] is None
        assert response_json["msg"] is None
    
    def test_user_leave_workspace_expired_access_token_raises(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo) -> None:
        """Test that if the access token has expired, an error will be raised."""

        user1, _ = login_user

        expired_access_token = create_token(user1.username, -1)

        client.post(
            "/api/workspace/",
            json = {
                "username": user1.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
            },
            headers={"Authorization": f"Bearer {expired_access_token}"}
        )

        response = client.delete(
            "/api/workspace/",
            json = {
                "username": user1.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
            },
            headers={"Authorization": f"Bearer {expired_access_token}"}
        )


        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        response_json = response.json()
        assert response_json["error"] == "TokenExpiredError"
        assert response_json["error_msg"] == "Token has expired."
        assert response_json["data"] is None
        assert response_json["msg"] is None

class TestUserLeaveWorkSpaceInputError:
    """Test the user leave workspace with input error."""

    def test_user_leave_workspace_no_workspace_exists_raises(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo) -> None:
        """Test that if the workspace does not exist, an error will be raised."""

        user1, access_token1 = login_user

        response = client.delete(
            "/api/workspace/",
            json = {
                "username": user1.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
            },
            headers={"Authorization": f"Bearer {access_token1}"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_json = response.json()
        assert response_json["error"] == "NotFoundError"
        assert response_json["error_msg"] == f'Workspace "{test_workspace_info.workspace_default_name}" not found.'
        assert response_json["msg"] is None
        assert response_json["data"] is None
    
    def test_user_leave_workspace_user_not_exists_raises(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo) -> None:
        """Test that if the user does not exist, an error will be raised."""
        
        user1, access_token1 = login_user

        user_does_not_exist = "user_does_not_exist"

        leaky_access_token = create_token(user_does_not_exist, 100)

        client.post(
            "/api/workspace/",
            json = {
                "username": user1.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
            },
            headers={"Authorization": f"Bearer {access_token1}"}
        )

        response = client.delete(
            "/api/workspace/",
            json = {
                "username": "user_does_not_exist",
                "workspace_default_name": test_workspace_info.workspace_default_name,

            },
            headers={"Authorization": f"Bearer {leaky_access_token}"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_json = response.json()
        assert response_json["error"] == "NotFoundError"
        assert response_json["error_msg"] == f'User "{user_does_not_exist}" not found.'
        assert response_json["msg"] is None
        assert response_json["data"] is None
    
    def test_user_leave_workspace_user_not_joined_raises(self, client: TestClient, login_users: Tuple[Tuple[TestUserInfo, str], Tuple[TestUserInfo, str]], test_workspace_info: TestWorkspaceInfo) -> None:
        """Test that if the workspace does not exist, an error will be raised."""
        
        user1, access_token1 = login_users[0]
        user2, access_token2 = login_users[1]

        client.post(
            "/api/workspace/",
            json = {
                "username": user1.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
            },
            headers={"Authorization": f"Bearer {access_token1}"}
        )

        response = client.delete(
            "/api/workspace/",
            json = {
                "username": user2.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
            },
            headers={"Authorization": f"Bearer {access_token2}"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_json = response.json()
        assert response_json["error"] == "NotFoundError"
        assert response_json["error_msg"] == f'User "{user2.username}" has not joined workspace "{test_workspace_info.workspace_default_name}".'
        assert response_json["msg"] is None
        assert response_json["data"] is None
