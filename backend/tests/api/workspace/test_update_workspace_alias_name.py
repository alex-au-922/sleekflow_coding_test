import time
from typing import Tuple
from fastapi import status
from fastapi.testclient import TestClient
import jwt # type: ignore
from config.auth_tokens_config import AUTH_TOKENS_CONFIG
from data_models import DatabaseConnection
from data_models.models import Account, WorkSpace, WorkSpaceAccountLink
from ...mock_data import TestUserInfo, TestWorkspaceInfo

def create_token(username: str, exp_time: int) -> str:
    """Return an expired token"""
    
    return jwt.encode({"username": username, "exp": time.time() + exp_time}, AUTH_TOKENS_CONFIG.secret_key, algorithm=AUTH_TOKENS_CONFIG.algorithm)

class TestChangeWorkspaceAlias():
    """Test that a user can change the alias of a workspace."""
   
    def test_user_change_workspace_alias(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo) -> None:
        """Test that a user can be invited to a workspace."""

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

        assert response.status_code == status.HTTP_202_ACCEPTED
        response_json = response.json()
        assert response_json["error"] is None
        assert response_json["error_msg"] is None
        assert response_json["data"] is None
        assert response_json["msg"] == f'User "{user1.username}" has changed the workspace "{test_workspace_info.workspace_default_name}" alias from "None" to "{test_workspace_info.workspace_alias}" successfully.'

        with DatabaseConnection() as db:
            query_user1: Account = db.query(Account).filter(Account.username == user1.username).one()
            workspace: WorkSpace = db.query(WorkSpace).filter(WorkSpace.workspace_default_name == test_workspace_info.workspace_default_name).one()
            workspace_account_record: WorkSpaceAccountLink = db.query(WorkSpaceAccountLink).filter(WorkSpaceAccountLink.user_id == query_user1.user_id, WorkSpaceAccountLink.workspace_id == workspace.workspace_id).one()
            assert workspace_account_record.locale_alias == test_workspace_info.workspace_alias
    
    def test_user_change_workspace_alias_idempotent(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo) -> None:
        """Test that a user can be invited to a workspace."""

        user1, access_token1 = login_user

        client.post(
            "/api/workspace/",
            json = {
                "username": user1.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
            },
            headers={"Authorization": f"Bearer {access_token1}"}
        )

        client.put(
            "/api/workspace/alias/",
            json = {
                "username": user1.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "new_workspace_alias": test_workspace_info.workspace_alias,
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

        assert response.status_code == status.HTTP_202_ACCEPTED
        response_json = response.json()
        assert response_json["error"] is None
        assert response_json["error_msg"] is None
        assert response_json["data"] is None
        assert response_json["msg"] == f'User "{user1.username}" has changed the workspace "{test_workspace_info.workspace_default_name}" alias from "{test_workspace_info.workspace_alias}" to "{test_workspace_info.workspace_alias}" successfully.'

        with DatabaseConnection() as db:
            query_user1: Account = db.query(Account).filter(Account.username == user1.username).one()
            workspace: WorkSpace = db.query(WorkSpace).filter(WorkSpace.workspace_default_name == test_workspace_info.workspace_default_name).one()
            workspace_account_record: WorkSpaceAccountLink = db.query(WorkSpaceAccountLink).filter(WorkSpaceAccountLink.user_id == query_user1.user_id, WorkSpaceAccountLink.workspace_id == workspace.workspace_id).one()
            assert workspace_account_record.locale_alias == test_workspace_info.workspace_alias
    
    def test_user_change_workspace_alias_independent(self, client: TestClient, login_users: Tuple[Tuple[TestUserInfo, str], Tuple[TestUserInfo, str]], test_workspace_info: TestWorkspaceInfo) -> None:
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

        user1_locale_alias = test_workspace_info.workspace_alias

        user1_response = client.put(
            "/api/workspace/alias/",
            json = {
                "username": user1.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "new_workspace_alias": user1_locale_alias,
            },
            headers={"Authorization": f"Bearer {access_token1}"}
        )

        assert user1_response.status_code == status.HTTP_202_ACCEPTED
        response_json = user1_response.json()
        assert response_json["error"] is None
        assert response_json["error_msg"] is None
        assert response_json["data"] is None
        assert response_json["msg"] == f'User "{user1.username}" has changed the workspace "{test_workspace_info.workspace_default_name}" alias from "{None}" to "{user1_locale_alias}" successfully.'

        user2_locale_alias = test_workspace_info.workspace_alias[::-1]

        user2_response = client.put(
            "/api/workspace/alias/",
            json = {
                "username": user2.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "new_workspace_alias": user2_locale_alias,
            },
            headers={"Authorization": f"Bearer {access_token2}"}
        )

        assert user2_response.status_code == status.HTTP_202_ACCEPTED
        response_json = user2_response.json()
        assert response_json["error"] is None
        assert response_json["error_msg"] is None
        assert response_json["data"] is None
        assert response_json["msg"] == f'User "{user2.username}" has changed the workspace "{test_workspace_info.workspace_default_name}" alias from "{None}" to "{user2_locale_alias}" successfully.'

        with DatabaseConnection() as db:
            query_user1: Account = db.query(Account).filter(Account.username == user1.username).one()
            workspace: WorkSpace = db.query(WorkSpace).filter(WorkSpace.workspace_default_name == test_workspace_info.workspace_default_name).one()
            workspace_account_record: WorkSpaceAccountLink = db.query(WorkSpaceAccountLink).filter(WorkSpaceAccountLink.user_id == query_user1.user_id, WorkSpaceAccountLink.workspace_id == workspace.workspace_id).one()
            assert workspace_account_record.locale_alias == user1_locale_alias
        
        with DatabaseConnection() as db:
            query_user2: Account = db.query(Account).filter(Account.username == user2.username).one()
            workspace = db.query(WorkSpace).filter(WorkSpace.workspace_default_name == test_workspace_info.workspace_default_name).one()
            workspace_account_record = db.query(WorkSpaceAccountLink).filter(WorkSpaceAccountLink.user_id == query_user2.user_id, WorkSpaceAccountLink.workspace_id == workspace.workspace_id).one()
            assert workspace_account_record.locale_alias == user2_locale_alias

class TestUsersleaveWorkspaceTokenError:
    """Test user leave workspace with token error"""

    def test_user_change_workspace_alias_no_access_token_raises(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo) -> None:
        """Test that a workspace cannot be created without access token."""

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
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        response_json = response.json()
        assert response_json["error"] == "UnauthorizedError"
        assert response_json["error_msg"] == "Unauthorized action."
        assert response_json["data"] is None
        assert response_json["msg"] is None
    
    def test_user_change_workspace_alias_wrong_access_token_raises(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo) -> None:
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

        response = client.put(
            "/api/workspace/alias/",
            json = {
                "username": user1.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "new_workspace_alias": test_workspace_info.workspace_alias,
            },
            headers={"Authorization": f"Bearer {access_token1}1"}
        )


        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        response_json = response.json()
        assert response_json["error"] == "InvalidTokenError"
        assert response_json["error_msg"] == "Invalid token."
        assert response_json["data"] is None
        assert response_json["msg"] is None
    
    def test_user_change_workspace_alias_expired_access_token_raises(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo) -> None:
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

        response = client.put(
            "/api/workspace/alias/",
            json = {
                "username": user1.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "new_workspace_alias": test_workspace_info.workspace_alias,
            },
            headers={"Authorization": f"Bearer {expired_access_token}"}
        )


        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        response_json = response.json()
        assert response_json["error"] == "TokenExpiredError"
        assert response_json["error_msg"] == "Token has expired."
        assert response_json["data"] is None
        assert response_json["msg"] is None

class TestUserChangeWorkSpaceAliasInputError:
    """Test the user change workspace alias with input error."""

    def test_change_workspace_user_not_exists_raises(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo) -> None:
        """Test that if the user does not exist, an error will be raised."""

        user, access_token = login_user

        user_does_not_exist = "user_does_not_exist"

        leaky_access_token = create_token(user_does_not_exist, 100)

        client.post(
            "/api/workspace/",
            json = {
                "username": user.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        response = client.put(
            "/api/workspace/alias/",
            json = {
                "username": user_does_not_exist,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "new_workspace_alias": test_workspace_info.workspace_alias,
            },
            headers={"Authorization": f"Bearer {leaky_access_token}"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_json = response.json()
        assert response_json["error"] == "NotFoundError"
        assert response_json["error_msg"] == f'User "{user_does_not_exist}" not found.'
        assert response_json["msg"] is None
        assert response_json["data"] is None

    def test_user_change_workspace_alias_no_workspace_exists_raises(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo) -> None:
        """Test that if the workspace does not exist, an error will be raised."""

        user1, access_token1 = login_user

        response = client.put(
            "/api/workspace/alias/",
            json = {
                "username": user1.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "new_workspace_alias": test_workspace_info.workspace_alias,
            },
            headers={"Authorization": f"Bearer {access_token1}"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_json = response.json()
        assert response_json["error"] == "NotFoundError"
        assert response_json["error_msg"] == f'Workspace "{test_workspace_info.workspace_default_name}" not found.'
        assert response_json["msg"] is None
        assert response_json["data"] is None
    
    def test_user_change_workspace_alias_not_joined_raises(self, client: TestClient, login_users: Tuple[Tuple[TestUserInfo, str], Tuple[TestUserInfo, str]], test_workspace_info: TestWorkspaceInfo) -> None:
        """Test that if the user is not joined to the workspace, an error will be raised."""

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

        response = client.put(
            "/api/workspace/alias/",
            json = {
                "username": user2.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "new_workspace_alias": test_workspace_info.workspace_alias,
            },
            headers={"Authorization": f"Bearer {access_token2}"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_json = response.json()
        assert response_json["error"] == "NotFoundError"
        assert response_json["error_msg"] == f'User "{user2.username}" not found in workspace "{test_workspace_info.workspace_default_name}".'
        assert response_json["msg"] is None
        assert response_json["data"] is None

