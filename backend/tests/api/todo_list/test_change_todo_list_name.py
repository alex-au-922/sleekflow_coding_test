from typing import Tuple
from fastapi import status
from fastapi.testclient import TestClient
from data_models import DatabaseConnection
from data_models.models import WorkSpace
import jwt # type: ignore
from config.auth_tokens_config import AUTH_TOKENS_CONFIG
import time
from ...mock_data import TestUserInfo, TestWorkspaceInfo, TestTodoListInfo

def create_token(username: str, exp_time: int) -> str:
    """Return an expired token"""
    
    return jwt.encode({"username": username, "exp": time.time() + exp_time}, AUTH_TOKENS_CONFIG.secret_key, algorithm=AUTH_TOKENS_CONFIG.algorithm)

class TestChangeTodoListName:
    """Test the change todolist name endpoint."""

    def test_workspace_owner_change_todo_list_name(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo, permuted_test_todolist_info: Tuple[TestTodoListInfo, TestTodoListInfo]) -> None:
        """Test that the workspace owner can change a todolist's name in the workspace."""
        user, access_token = login_user
        todolist_info1, todolist_info2 = permuted_test_todolist_info

        client.post(
            "/api/workspace/",
            json = {
                "username": user.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        create_response = client.post(
            "/api/workspace/todolist/",
            json = {
                "username": user.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_name": todolist_info1.todolist_name,
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        response = client.put(
            "/api/workspace/todolist/",
            json = {
                "username": user.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_id": int(create_response.json()["data"]),
                "new_todolist_name": todolist_info2.todolist_name,
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == status.HTTP_202_ACCEPTED
        response_json = response.json()
        assert response_json["error"] is None
        assert response_json["error_msg"] is None
        assert response_json["data"] is None
        assert response_json["msg"] == f'User "{user.username}" has changed the name of todolist from "{todolist_info1.todolist_name}" to "{todolist_info2.todolist_name}" in workspace "{test_workspace_info.workspace_default_name}" successfully.'

    
    def test_workspace_member_change_todo_list_name(self, client: TestClient, login_users: Tuple[Tuple[TestUserInfo, str], Tuple[TestUserInfo, str]], test_workspace_info: TestWorkspaceInfo, permuted_test_todolist_info: Tuple[TestTodoListInfo, TestTodoListInfo]) -> None:
        """Test that a workspace member can change a todolist's name in the workspace."""
        user1, access_token1 = login_users[0]
        user2, access_token2 = login_users[1]

        todolist_info1, todolist_info2 = permuted_test_todolist_info

        client.post(
            "/api/workspace/",
            json = {
                "username": user1.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
            },
            headers={"Authorization": f"Bearer {access_token1}"}
        )

        response = client.put(
            "/api/workspace/invite/",
            json = {
                "owner_username": user1.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "invitee_username": user2.username,
            },
            headers={"Authorization": f"Bearer {access_token1}"}
        )

        with DatabaseConnection() as db:
            workspace: WorkSpace = db.query(WorkSpace).filter(WorkSpace.workspace_default_name == test_workspace_info.workspace_default_name).one()
            
            assert len(workspace.members) == 2

        create_response = client.post(
            "/api/workspace/todolist/",
            json = {
                "username": user2.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_name": todolist_info1.todolist_name,
            },
            headers={"Authorization": f"Bearer {access_token2}"}
        )

        response = client.put(
            "/api/workspace/todolist/",
            json = {
                "username": user2.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_id": int(create_response.json()["data"]),
                "new_todolist_name": todolist_info2.todolist_name,
            },
            headers={"Authorization": f"Bearer {access_token2}"}
        )

        assert response.status_code == status.HTTP_202_ACCEPTED
        response_json = response.json()
        assert response_json["error"] is None
        assert response_json["error_msg"] is None
        assert response_json["data"] is None
        assert response_json["msg"] == f'User "{user2.username}" has changed the name of todolist from "{todolist_info1.todolist_name}" to "{todolist_info2.todolist_name}" in workspace "{test_workspace_info.workspace_default_name}" successfully.'

class TestDeleteTodoListTokenError:
    """Test the delete todolist with token error."""

    def test_change_todo_list_name_no_access_token_raises(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo, permuted_test_todolist_info: Tuple[TestTodoListInfo, TestTodoListInfo]) -> None:
        """Test that the name of todo list cannot be changed without access token."""
        
        user, access_token = login_user
        todolist_info1, todolist_info2 = permuted_test_todolist_info
        
        client.post(
            "/api/workspace/",
            json = {
                "username": user.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        create_response = client.post(
            "/api/workspace/todolist/",
            json = {
                "username": user.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_name": todolist_info1.todolist_name,
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        response = client.put(
            "/api/workspace/todolist/",
            json = {
                "username": user.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_id": int(create_response.json()["data"]),
                "new_todolist_name": todolist_info2.todolist_name,
            },
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        response_json = response.json()
        assert response_json["error"] == "UnauthorizedError"
        assert response_json["error_msg"] == "Unauthorized action."
        assert response_json["data"] is None
        assert response_json["msg"] is None
    
    def test_change_todo_list_name_wrong_access_token_raises(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo, permuted_test_todolist_info: Tuple[TestTodoListInfo, TestTodoListInfo]) -> None:
        """Test that if the access token is wrong, an error will be raised."""
        user, access_token = login_user
        todolist_info1, todolist_info2 = permuted_test_todolist_info

        client.post(
            "/api/workspace/",
            json = {
                "username": user.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        create_response = client.post(
            "/api/workspace/todolist/",
            json = {
                "username": user.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_name": todolist_info1.todolist_name,
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        response = client.put(
            "/api/workspace/todolist/",
            json = {
                "username": user.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_id": int(create_response.json()["data"]),
                "new_todolist_name": todolist_info2.todolist_name,
            },
            headers={"Authorization": f"Bearer {access_token}1"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        response_json = response.json()
        assert response_json["error"] == "InvalidTokenError"
        assert response_json["error_msg"] == "Invalid token."
        assert response_json["data"] is None
        assert response_json["msg"] is None
    
    def test_change_todo_list_name_expired_access_token_raises(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo, permuted_test_todolist_info: Tuple[TestTodoListInfo, TestTodoListInfo]) -> None:
        """Test that if the access token has expired, an error will be raised."""

        user, access_token = login_user
        todolist_info1, todolist_info2 = permuted_test_todolist_info

        expired_access_token = create_token(user.username, -1)

        client.post(
            "/api/workspace/",
            json = {
                "username": user.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        create_response = client.post(
            "/api/workspace/todolist/",
            json = {
                "username": user.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_name": todolist_info1.todolist_name,
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        response = client.put(
            "/api/workspace/todolist/",
            json = {
                "username": user.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_id": int(create_response.json()["data"]),
                "new_todolist_name": todolist_info2.todolist_name,
            },
            headers={"Authorization": f"Bearer {expired_access_token}"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        response_json = response.json()
        assert response_json["error"] == "TokenExpiredError"
        assert response_json["error_msg"] == "Token has expired."
        assert response_json["data"] is None
        assert response_json["msg"] is None

class TestUserDeleteTodoListInputError:
    """Test the user create todo list with input error."""

    def test_user_change_todo_list_name_no_workspace_exists_raises(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo, permuted_test_todolist_info: Tuple[TestTodoListInfo, TestTodoListInfo]) -> None:
        """Test that if the workspace does not exist, an error will be raised."""

        user, access_token = login_user
        todolist_info1, todolist_info2 = permuted_test_todolist_info

        client.post(
            "/api/workspace/",
            json = {
                "username": user.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        create_response = client.post(
            "/api/workspace/todolist/",
            json = {
                "username": user.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_name": todolist_info1.todolist_name,
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        non_existing_workspace_name = "non_existing_workspace_name"

        response = client.put(
            "/api/workspace/todolist/",
            json = {
                "username": user.username,
                "workspace_default_name": non_existing_workspace_name,
                "todolist_id": int(create_response.json()["data"]),
                "new_todolist_name": todolist_info2.todolist_name,
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_json = response.json()
        assert response_json["error"] == "NotFoundError"
        assert response_json["error_msg"] == f'Workspace "{non_existing_workspace_name}" not found.'
        assert response_json["msg"] is None
        assert response_json["data"] is None
    
    def test_user_change_todo_list_name_user_not_exists_raises(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo, permuted_test_todolist_info: Tuple[TestTodoListInfo, TestTodoListInfo]) -> None:
        """Test that if the user does not exist, an error will be raised."""
        
        user, access_token = login_user
        todolist_info1, todolist_info2 = permuted_test_todolist_info

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

        create_response = client.post(
            "/api/workspace/todolist/",
            json = {
                "username": user.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_name": todolist_info1.todolist_name,
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        response = client.put(
            "/api/workspace/todolist/",
            json = {
                "username": user_does_not_exist,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_id": int(create_response.json()["data"]),
                "new_todolist_name": todolist_info2.todolist_name,
            },
            headers={"Authorization": f"Bearer {leaky_access_token}"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_json = response.json()
        assert response_json["error"] == "NotFoundError"
        assert response_json["error_msg"] == f'User "{user_does_not_exist}" not found.'
        assert response_json["msg"] is None
        assert response_json["data"] is None
    
    def test_user_change_todo_list_name_user_not_joined_raises(self, client: TestClient, login_users: Tuple[Tuple[TestUserInfo, str], Tuple[TestUserInfo, str]], test_workspace_info: TestWorkspaceInfo , permuted_test_todolist_info: Tuple[TestTodoListInfo, TestTodoListInfo]) -> None:
        """Test that if the workspace does not exist, an error will be raised."""
        
        user1, access_token1 = login_users[0]
        user2, access_token2 = login_users[1]
        todolist_info1, todolist_info2 = permuted_test_todolist_info

        client.post(
            "/api/workspace/",
            json = {
                "username": user1.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
            },
            headers={"Authorization": f"Bearer {access_token1}"}
        )

        create_response = client.post(
            "/api/workspace/todolist/",
            json = {
                "username": user1.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_name": todolist_info1.todolist_name,
            },
            headers={"Authorization": f"Bearer {access_token1}"}
        )

        response = client.put(
            "/api/workspace/todolist/",
            json = {
                "username": user2.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_id": int(create_response.json()["data"]),
                "new_todolist_name": todolist_info2.todolist_name,
            },
            headers={"Authorization": f"Bearer {access_token2}"}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_json = response.json()
        assert response_json["error"] == "NotFoundError"
        assert response_json["error_msg"] == f'User "{user2.username}" has not joined workspace "{test_workspace_info.workspace_default_name}".'
        assert response_json["msg"] is None
        assert response_json["data"] is None
    
    def test_user_change_todo_list_name_not_exists_raises(self, client: TestClient, login_user:Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo, permuted_test_todolist_info: Tuple[TestTodoListInfo, TestTodoListInfo]) -> None:
        """Test that if the todo list does not exist in the workspace, an error will be raised."""
        
        user, access_token = login_user
        todolist_info1, todolist_info2 = permuted_test_todolist_info

        client.post(
            "/api/workspace/",
            json = {
                "username": user.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        create_response = client.post(
            "/api/workspace/todolist/",
            json = {
                "username": user.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_name": todolist_info1.todolist_name,
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        todolist_id_not_exists = int(create_response.json()["data"]) + 1

        response = client.put(
            "/api/workspace/todolist/",
            json = {
                "username": user.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_id": todolist_id_not_exists,
                "new_todolist_name": todolist_info2.todolist_name,
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_json = response.json()
        assert response_json["error"] == "NotFoundError"
        assert response_json["error_msg"] == f'Todo list "{todolist_id_not_exists}" not found.'
        assert response_json["msg"] is None
        assert response_json["data"] is None
