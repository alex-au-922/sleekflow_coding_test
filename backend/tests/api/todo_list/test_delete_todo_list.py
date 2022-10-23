from typing import Tuple
from fastapi import status
from fastapi.testclient import TestClient
from data_models import DatabaseConnection
from data_models.models import Todo, WorkSpace
import jwt # type: ignore
from config.auth_tokens_config import AUTH_TOKENS_CONFIG
import time
from ...mock_data import TestUserInfo, TestWorkspaceInfo, TestTodoListInfo

def create_token(username: str, exp_time: int) -> str:
    """Return an expired token"""
    
    return jwt.encode({"username": username, "exp": time.time() + exp_time}, AUTH_TOKENS_CONFIG.secret_key, algorithm=AUTH_TOKENS_CONFIG.algorithm)


class TestDeleteTodoList:
    """Test the delete todolist endpoint."""

    def test_workspace_owner_delete_todo_list(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo, test_todolist_info: TestTodoListInfo) -> None:
        """Test that a workspace owner can delete a todolist in the workspace."""
        user, access_token = login_user

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
                "todolist_name": test_todolist_info.todolist_name,
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        response = client.delete(
            "/api/workspace/todolist/?username={}&workspace_default_name={}&todolist_id={}".format(user.username, test_workspace_info.workspace_default_name, int(create_response.json()["data"])),
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == status.HTTP_202_ACCEPTED
        response_json = response.json()
        assert response_json["error"] is None
        assert response_json["error_msg"] is None
        assert response_json["data"] is None
        assert response_json["msg"] == f'User "{user.username}" has deleted todolist "{test_todolist_info.todolist_name}" in workspace "{test_workspace_info.workspace_default_name}" successfully.'

    
    def test_workspace_member_delete_todo_list(self, client: TestClient, login_users: Tuple[Tuple[TestUserInfo, str], Tuple[TestUserInfo, str]], test_workspace_info: TestWorkspaceInfo, test_todolist_info: TestTodoListInfo) -> None:
        """Test that a workspace member can delete a todolist in the workspace."""
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
                "todolist_name": test_todolist_info.todolist_name,
            },
            headers={"Authorization": f"Bearer {access_token2}"}
        )

        response = client.delete(
            "/api/workspace/todolist/?username={}&workspace_default_name={}&todolist_id={}".format(user2.username, test_workspace_info.workspace_default_name, int(create_response.json()["data"])),
            headers={"Authorization": f"Bearer {access_token2}"}
        )

        assert response.status_code == status.HTTP_202_ACCEPTED
        response_json = response.json()
        assert response_json["error"] is None
        assert response_json["error_msg"] is None
        assert response_json["data"] is None
        assert response_json["msg"] == f'User "{user2.username}" has deleted todolist "{test_todolist_info.todolist_name}" in workspace "{test_workspace_info.workspace_default_name}" successfully.'

class TestDeleteTodoListTokenError:
    """Test the delete todolist with token error."""

    def test_delete_todo_list_no_access_token_raises(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo, test_todolist_info: TestTodoListInfo) -> None:
        """Test that a todo list cannot be deleted without access token."""
        
        user, access_token = login_user
        
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
                "todolist_name": test_todolist_info.todolist_name,
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        response = client.delete(
            "/api/workspace/todolist/?username={}&workspace_default_name={}&todolist_id={}".format(user.username, test_workspace_info.workspace_default_name, int(create_response.json()["data"])),
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        response_json = response.json()
        assert response_json["error"] == "UnauthorizedError"
        assert response_json["error_msg"] == "Unauthorized action."
        assert response_json["data"] is None
        assert response_json["msg"] is None
    
    def test_delete_todo_list_wrong_access_token_raises(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo, test_todolist_info: TestTodoListInfo) -> None:
        """Test that if the access token is wrong, an error will be raised."""
        user, access_token = login_user

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
                "todolist_name": test_todolist_info.todolist_name,
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        response = client.delete(
            "/api/workspace/todolist/?username={}&workspace_default_name={}&todolist_id={}".format(user.username, test_workspace_info.workspace_default_name, int(create_response.json()["data"])),
            headers={"Authorization": f"Bearer {access_token}1"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        response_json = response.json()
        assert response_json["error"] == "InvalidTokenError"
        assert response_json["error_msg"] == "Invalid token."
        assert response_json["data"] is None
        assert response_json["msg"] is None
    
    def test_delete_todo_list_expired_access_token_raises(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo, test_todolist_info: TestTodoListInfo) -> None:
        """Test that if the access token has expired, an error will be raised."""

        user, access_token = login_user

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
                "todolist_name": test_todolist_info.todolist_name,
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        response = client.delete(
            "/api/workspace/todolist/?username={}&workspace_default_name={}&todolist_id={}".format(user.username, test_workspace_info.workspace_default_name, int(create_response.json()["data"])),
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

    def test_user_delete_todo_list_no_workspace_exists_raises(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo, test_todolist_info: TestTodoListInfo) -> None:
        """Test that if the workspace does not exist, an error will be raised."""

        user, access_token = login_user

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
                "todolist_name": test_todolist_info.todolist_name,
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        non_existing_workspace_name = "non_existing_workspace_name"

        response = client.delete(
            "/api/workspace/todolist/?username={}&workspace_default_name={}&todolist_id={}".format(user.username, non_existing_workspace_name, int(create_response.json()["data"])),
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_json = response.json()
        assert response_json["error"] == "NotFoundError"
        assert response_json["error_msg"] == f'Workspace "{non_existing_workspace_name}" not found.'
        assert response_json["msg"] is None
        assert response_json["data"] is None
    
    def test_user_delete_todo_list_user_not_exists_raises(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo, test_todolist_info: TestTodoListInfo) -> None:
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

        create_response = client.post(
            "/api/workspace/todolist/",
            json = {
                "username": user.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_name": test_todolist_info.todolist_name,
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        response = client.delete(
            "/api/workspace/todolist/?username={}&workspace_default_name={}&todolist_id={}".format(user_does_not_exist, test_workspace_info.workspace_default_name, int(create_response.json()["data"])),
            headers={"Authorization": f"Bearer {leaky_access_token}"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_json = response.json()
        assert response_json["error"] == "NotFoundError"
        assert response_json["error_msg"] == f'User "{user_does_not_exist}" not found.'
        assert response_json["msg"] is None
        assert response_json["data"] is None
    
    def test_user_delete_todo_list_user_not_joined_raises(self, client: TestClient, login_users: Tuple[Tuple[TestUserInfo, str], Tuple[TestUserInfo, str]], test_workspace_info: TestWorkspaceInfo, test_todolist_info: TestTodoListInfo) -> None:
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

        create_response = client.post(
            "/api/workspace/todolist/",
            json = {
                "username": user1.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_name": test_todolist_info.todolist_name,
            },
            headers={"Authorization": f"Bearer {access_token1}"}
        )

        response = client.delete(
            "/api/workspace/todolist/?username={}&workspace_default_name={}&todolist_id={}".format(user2.username, test_workspace_info.workspace_default_name, int(create_response.json()["data"])),
            headers={"Authorization": f"Bearer {access_token2}"}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_json = response.json()
        assert response_json["error"] == "NotFoundError"
        assert response_json["error_msg"] == f'User "{user2.username}" has not joined workspace "{test_workspace_info.workspace_default_name}".'
        assert response_json["msg"] is None
        assert response_json["data"] is None
    
    def test_user_delete_todo_list_not_exists_raises(self, client: TestClient, login_user:Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo, test_todolist_info: TestTodoListInfo) -> None:
        """Test that if the todo list does not exist in the workspace, an error will be raised."""
        
        user, access_token = login_user

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
                "todolist_name": test_todolist_info.todolist_name,
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        todolist_id_not_exists = int(create_response.json()["data"]) + 1

        response = client.delete(
            "/api/workspace/todolist/?username={}&workspace_default_name={}&todolist_id={}".format(user.username, test_workspace_info.workspace_default_name, todolist_id_not_exists),
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_json = response.json()
        assert response_json["error"] == "NotFoundError"
        assert response_json["error_msg"] == f'Todo list of id "{todolist_id_not_exists}" not found.'
        assert response_json["msg"] is None
        assert response_json["data"] is None

class TestDeleteTodoListDeleteTodo:
    """Test the delete todo list will also delete todo."""

    def test_delete_todolist_delete_todo(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo, test_todolist_info: TestTodoListInfo) -> None:
        """Test that if the todo list is deleted, the todo in the todo list will also be deleted."""

        user, access_token = login_user
        
        client.post(
            "/api/workspace/",
            json = {
                "username": user.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        create_todolist_response = client.post(
            "/api/workspace/todolist/",
            json = {
                "username": user.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_name": test_todolist_info.todolist_name,
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        created_todo_response = client.post(
            "/api/workspace/todolist/todo/",
            json = {
                "username": user.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_id": int(create_todolist_response.json()["data"]),
                "todo_name": "testing",
                "todo_description": "testing",
                "todo_due_date": "2021-01-01",
                "todo_status": "created",
                "todo_priority": "high",
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )


        response = client.delete(
            "/api/workspace/todolist/?username={}&workspace_default_name={}&todolist_id={}".format(user.username, test_workspace_info.workspace_default_name, int(create_todolist_response.json()["data"])),
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == status.HTTP_202_ACCEPTED
        response_json = response.json()
        assert response_json["error"] is None
        assert response_json["error_msg"] is None
        assert response_json["data"] is None
        assert response_json["msg"] == f'User "{user.username}" has deleted todolist "{test_todolist_info.todolist_name}" in workspace "{test_workspace_info.workspace_default_name}" successfully.'

        with DatabaseConnection() as db:
            todo: Todo = db.query(Todo).filter(Todo.todo_id==int(created_todo_response.json()["data"])).one_or_none()
            assert todo is None
        