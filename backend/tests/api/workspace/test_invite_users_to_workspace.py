import time
from typing import Tuple
import pytest
from fastapi import status
from fastapi.testclient import TestClient
import jwt # type: ignore
from config.auth_tokens_config import AUTH_TOKENS_CONFIG
from data_models import DatabaseConnection
from data_models.models import Account, WorkSpace, WorkSpaceAccountLink

class TestUserInfo:
    username: str
    email: str
    password: str

def create_token(username: str, exp_time: int) -> str:
    """Return an expired token"""
    
    return jwt.encode({"username": username, "exp": time.time() + exp_time}, AUTH_TOKENS_CONFIG.secret_key, algorithm=AUTH_TOKENS_CONFIG.algorithm)

class TestInviteUsersToWorkspace():
    """Test inviting a user to a workspace"""

    def test_invite_user_to_workspace(self, client: TestClient, login_users: Tuple[Tuple[TestUserInfo, str], Tuple[TestUserInfo, str]]) -> None:
        """Test that a user can be invited to a workspace."""

        user1, access_token1 = login_users[0]
        user2, _ = login_users[1]

        client.post(
            "/api/workspace/",
            json = {
                "username": user1.username,
                "workspace_default_name": "workspace_testing",
            },
            headers={"Authorization": f"Bearer {access_token1}"}
        )

        response = client.put(
            "/api/workspace/invite/",
            json = {
                "owner_username": user1.username,
                "workspace_default_name": "workspace_testing",
                "invitee_username": user2.username,
            },
            headers={"Authorization": f"Bearer {access_token1}"}
        )

        assert response.status_code == status.HTTP_202_ACCEPTED
        response_json = response.json()
        assert response_json["error"] is None
        assert response_json["error_msg"] is None
        assert response_json["data"] is None
        assert response_json["msg"] == f'Invited user "{user2.username}" to workspace "workspace_testing" successfully.'

        with DatabaseConnection() as db:
            workspace: WorkSpace = db.query(WorkSpace).filter(WorkSpace.workspace_default_name == "workspace_testing").one()
            
            member: WorkSpaceAccountLink
            for member in workspace.members:
                user: Account = db.query(Account).filter(Account.user_id == member.user_id).one()
                assert user.username in [user1.username, user2.username]
            
            assert len(workspace.members) == 2

class TestInviteUsersToWorkspaceTokenError:
    """Test invite users to workspace with token error"""

    def test_invite_workspace_no_access_token_raises(self, client: TestClient, login_users: Tuple[Tuple[TestUserInfo, str], Tuple[TestUserInfo, str]]) -> None:
        """Test that a workspace cannot be created without access token."""

        user1, access_token1 = login_users[0]
        user2, _ = login_users[1]

        client.post(
            "/api/workspace/",
            json = {
                "username": user1.username,
                "workspace_default_name": "workspace_testing",
            },
            headers={"Authorization": f"Bearer {access_token1}"}
        )

        response = client.put(
            "/api/workspace/invite/",
            json = {
                "owner_username": user1.username,
                "workspace_default_name": "workspace_testing",
                "invitee_username": user2.username,
            },
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        response_json = response.json()
        assert response_json["error"] == "UnauthorizedError"
        assert response_json["error_msg"] == "Unauthorized action."
        assert response_json["data"] is None
        assert response_json["msg"] is None
    
    def test_create_workspace_wrong_access_token_raises(self, client: TestClient, login_users: Tuple[Tuple[TestUserInfo, str], Tuple[TestUserInfo, str]]) -> None:
        """Test that if the access token is wrong, an error will be raised."""

        user1, access_token1 = login_users[0]
        user2, _ = login_users[1]

        client.post(
            "/api/workspace/",
            json = {
                "username": user1.username,
                "workspace_default_name": "workspace_testing",
            },
            headers={"Authorization": f"Bearer {access_token1}"}
        )

        response = client.put(
            "/api/workspace/invite/",
            json = {
                "owner_username": user1.username,
                "workspace_default_name": "workspace_testing",
                "invitee_username": user2.username,
            },
            headers={"Authorization": f"Bearer {access_token1}1"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        response_json = response.json()
        assert response_json["error"] == "InvalidTokenError"
        assert response_json["error_msg"] == "Invalid token."
        assert response_json["data"] is None
        assert response_json["msg"] is None
    
    def test_create_workspace_expired_access_token_raises(self, client: TestClient, login_users: Tuple[Tuple[TestUserInfo, str], Tuple[TestUserInfo, str]]) -> None:
        """Test that if the access token has expired, an error will be raised."""

        user1, _ = login_users[0]
        user2, _ = login_users[1]

        expired_access_token = create_token("testing", -1)

        client.post(
            "/api/workspace/",
            json = {
                "username": user1.username,
                "workspace_default_name": "workspace_testing",
            },
            headers={"Authorization": f"Bearer {expired_access_token}"}
        )

        response = client.put(
            "/api/workspace/invite/",
            json = {
                "owner_username": user1.username,
                "workspace_default_name": "workspace_testing",
                "invitee_username": user2.username,
            },
            headers={"Authorization": f"Bearer {expired_access_token}"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        response_json = response.json()
        assert response_json["error"] == "TokenExpiredError"
        assert response_json["error_msg"] == "Token has expired."
        assert response_json["data"] is None
        assert response_json["msg"] is None

class TestInviteUsersToWorkSpaceInputError:
    """Test the invite user to workspace with input error."""

    def test_invite_workspace_not_owner_raises(self, client: TestClient, login_users: Tuple[Tuple[TestUserInfo, str], Tuple[TestUserInfo, str]]) -> None:
        """Test that if the owner is not the owner, an error will be raised."""

        user1, access_token1 = login_users[0]
        user2, access_token2 = login_users[1]

        client.post(
            "/api/workspace/",
            json = {
                "username": user1.username,
                "workspace_default_name": "workspace_testing",
            },
            headers={"Authorization": f"Bearer {access_token1}"}
        )

        response = client.put(
            "/api/workspace/invite/",
            json = {
                "owner_username": user2.username,
                "workspace_default_name": "workspace_testing",
                "invitee_username": user1.username,
            },
            headers={"Authorization": f"Bearer {access_token2}"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        response_json = response.json()
        assert response_json["error"] == "UnauthorizedError"
        assert response_json["error_msg"] == f'Unauthorized action.'
        assert response_json["msg"] is None
        assert response_json["data"] is None

    def test_invite_user_workspace_no_workspace_exists_raises(self, client: TestClient, login_users: Tuple[Tuple[TestUserInfo, str], Tuple[TestUserInfo, str]]) -> None:
        """Test that if the workspace does not exist, an error will be raised."""

        user1, access_token1 = login_users[0]
        user2, _ = login_users[1]

        response = client.put(
            "/api/workspace/invite/",
            json = {
                "owner_username": user1.username,
                "workspace_default_name": "workspace_testing",
                "invitee_username": user2.username,
            },
            headers={"Authorization": f"Bearer {access_token1}"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_json = response.json()
        assert response_json["error"] == "NotFoundError"
        assert response_json["error_msg"] == f'Workspace "workspace_testing" not found.'
        assert response_json["msg"] is None
        assert response_json["data"] is None
    
    def test_invite_user_workspace_no_invitee_exists_raises(self, client: TestClient, login_user: Tuple[TestUserInfo, str]) -> None:
        """Test that if the workspace does not exist, an error will be raised."""
        
        user1, access_token1 = login_user

        client.post(
            "/api/workspace/",
            json = {
                "username": user1.username,
                "workspace_default_name": "workspace_testing",
            },
            headers={"Authorization": f"Bearer {access_token1}"}
        )

        response = client.put(
            "/api/workspace/invite/",
            json = {
                "owner_username": user1.username,
                "workspace_default_name": "workspace_testing",
                "invitee_username": "123547819239872",
            },
            headers={"Authorization": f"Bearer {access_token1}"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_json = response.json()
        assert response_json["error"] == "NotFoundError"
        assert response_json["error_msg"] == f'User "123547819239872" not found.'
        assert response_json["msg"] is None
        assert response_json["data"] is None
    
    def test_invite_user_workspace_invitee_already_joined_raises(self, client: TestClient, login_users: Tuple[Tuple[TestUserInfo, str], Tuple[TestUserInfo, str]]) -> None:
        """Test that if the workspace does not exist, an error will be raised."""

        user1, access_token1 = login_users[0]
        user2, _ = login_users[1]

        client.post(
            "/api/workspace/",
            json = {
                "username": user1.username,
                "workspace_default_name": "workspace_testing",
            },
            headers={"Authorization": f"Bearer {access_token1}"}
        )

        client.put(
            "/api/workspace/invite/",
            json = {
                "owner_username": user1.username,
                "workspace_default_name": "workspace_testing",
                "invitee_username": user2.username
            },
            headers={"Authorization": f"Bearer {access_token1}"}
        )

        response = client.put(
            "/api/workspace/invite/",
            json = {
                "owner_username": user1.username,
                "workspace_default_name": "workspace_testing",
                "invitee_username": user2.username,
            },
            headers={"Authorization": f"Bearer {access_token1}"}
        )

        assert response.status_code == status.HTTP_409_CONFLICT
        response_json = response.json()
        assert response_json["error"] == "DuplicateError"
        assert response_json["error_msg"] == f'User "{user2.username}" has already joined workspace "workspace_testing".'
        assert response_json["msg"] is None
        assert response_json["data"] is None
