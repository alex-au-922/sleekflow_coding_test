import datetime
from typing import Tuple
from fastapi import status
from fastapi.testclient import TestClient
from data_models import DatabaseConnection
from data_models.models import WorkSpace, Todo
import jwt # type: ignore
import pytest
from config.auth_tokens_config import AUTH_TOKENS_CONFIG
import time
from ...mock_data import TestUserInfo, TestWorkspaceInfo, TestTodoListInfo

def create_token(username: str, exp_time: int) -> str:
    """Return an expired token"""
    
    return jwt.encode({"username": username, "exp": time.time() + exp_time}, AUTH_TOKENS_CONFIG.secret_key, algorithm=AUTH_TOKENS_CONFIG.algorithm)


class TestDeleteTodo:
    """Test the change todo endpoint."""

    def test_workspace_owner_delete_todo(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo, test_todolist_info: TestTodoListInfo) -> None:
        """Test that a workspace owner can delete a todo in the workspace in the todolist."""
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

        create_todo_response = client.post(
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

        with DatabaseConnection() as db:
            result: Todo = db.query(Todo).filter(Todo.name == "testing", Todo.todolist_id == int(create_todolist_response.json()["data"])).one()
            assert result.todo_id == int(create_todo_response.json()["data"])
            assert result.name == "testing"
            assert result.description == "testing"
            assert result.due_date == datetime.datetime(2021, 1, 1)
            assert result.status == "created"
            assert result.priority == "high"
    

        response = client.delete(
            "/api/workspace/todolist/todo/?username={}&workspace_default_name={}&todolist_id={}&todo_id={}".format(user.username, test_workspace_info.workspace_default_name, create_todolist_response.json()["data"], create_todo_response.json()["data"]),
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == status.HTTP_202_ACCEPTED
        response_json = response.json()
        assert response_json["error"] is None
        assert response_json["error_msg"] is None
        assert response_json["data"] is None
        assert response_json["msg"] == f'Todo "testing" has been deleted in todo list "{test_todolist_info.todolist_name}" in workspace "{test_workspace_info.workspace_default_name}" successfully.'

        with DatabaseConnection() as db:
            result = db.query(Todo).filter(Todo.name == "testing", Todo.todolist_id == int(create_todolist_response.json()["data"])).one_or_none()
            assert result is None
    
    def test_workspace_member_delete_todo(self, client: TestClient, login_users: Tuple[Tuple[TestUserInfo, str], Tuple[TestUserInfo, str]], test_workspace_info: TestWorkspaceInfo, test_todolist_info: TestTodoListInfo) -> None:
        """Test that a workspace member can delete a todo in the workspace in the todolist."""
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

        create_todolist_response = client.post(
            "/api/workspace/todolist/",
            json = {
                "username": user2.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_name": test_todolist_info.todolist_name,
            },
            headers={"Authorization": f"Bearer {access_token2}"}
        )


        create_todo_response = client.post(
            "/api/workspace/todolist/todo/",
            json = {
                "username": user1.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_id": int(create_todolist_response.json()["data"]),
                "todo_name": "testing",
                "todo_description": "testing",
                "todo_due_date": "2021-01-01",
                "todo_status": "created",
                "todo_priority": "high",
            },
            headers={"Authorization": f"Bearer {access_token1}"}
        )

        with DatabaseConnection() as db:
            result: Todo = db.query(Todo).filter(Todo.name == "testing", Todo.todolist_id == int(create_todolist_response.json()["data"])).one()
            assert result.todo_id == int(create_todo_response.json()["data"])
            assert result.name == "testing"
            assert result.description == "testing"
            assert result.due_date == datetime.datetime(2021, 1, 1)
            assert result.status == "created"
            assert result.priority == "high"
    

        response = client.delete(
            "/api/workspace/todolist/todo/?username={}&workspace_default_name={}&todolist_id={}&todo_id={}".format(user2.username, test_workspace_info.workspace_default_name, create_todolist_response.json()["data"], create_todo_response.json()["data"]),
            headers={"Authorization": f"Bearer {access_token2}"}
        )

        assert response.status_code == status.HTTP_202_ACCEPTED
        response_json = response.json()
        assert response_json["error"] is None
        assert response_json["error_msg"] is None
        assert response_json["data"] is None
        assert response_json["msg"] == f'Todo "testing" has been deleted in todo list "{test_todolist_info.todolist_name}" in workspace "{test_workspace_info.workspace_default_name}" successfully.'

        with DatabaseConnection() as db:
            result = db.query(Todo).filter(Todo.name == "testing", Todo.todolist_id == int(create_todolist_response.json()["data"])).one_or_none()
            assert result is None

class TestCreateTodoTokenError:
    """Test the create todo with token error."""

    def test_change_todo_no_access_token_raises(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo, test_todolist_info: TestTodoListInfo) -> None:
        """Test that a workspace cannot be created without access token."""
        
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

        create_todo_response = client.post(
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
            "/api/workspace/todolist/todo/?username={}&workspace_default_name={}&todolist_id={}&todo_id={}".format(user.username, test_workspace_info.workspace_default_name, create_todolist_response.json()["data"], create_todo_response.json()["data"]),
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        response_json = response.json()
        assert response_json["error"] == "UnauthorizedError"
        assert response_json["error_msg"] == "Unauthorized action."
        assert response_json["data"] is None
        assert response_json["msg"] is None
    
    def test_create_todo_list_wrong_access_token_raises(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo, test_todolist_info: TestTodoListInfo) -> None:
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

        create_todolist_response = client.post(
            "/api/workspace/todolist/",
            json = {
                "username": user.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_name": test_todolist_info.todolist_name,
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        create_todo_response = client.post(
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
            "/api/workspace/todolist/todo/?username={}&workspace_default_name={}&todolist_id={}&todo_id={}".format(user.username, test_workspace_info.workspace_default_name, create_todolist_response.json()["data"], create_todo_response.json()["data"]),
            headers={"Authorization": f"Bearer {access_token}1"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        response_json = response.json()
        assert response_json["error"] == "InvalidTokenError"
        assert response_json["error_msg"] == "Invalid token."
        assert response_json["data"] is None
        assert response_json["msg"] is None
    
    def test_create_todo_list_expired_access_token_raises(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo, test_todolist_info: TestTodoListInfo) -> None:
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

        create_todolist_response = client.post(
            "/api/workspace/todolist/",
            json = {
                "username": user.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_name": test_todolist_info.todolist_name,
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        create_todo_response = client.post(
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
            "/api/workspace/todolist/todo/?username={}&workspace_default_name={}&todolist_id={}&todo_id={}".format(user.username, test_workspace_info.workspace_default_name, create_todolist_response.json()["data"], create_todo_response.json()["data"]),
            headers={"Authorization": f"Bearer {expired_access_token}"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        response_json = response.json()
        assert response_json["error"] == "TokenExpiredError"
        assert response_json["error_msg"] == "Token has expired."
        assert response_json["data"] is None
        assert response_json["msg"] is None

class TestUserChangeTodoInputError:
    """Test the user change a todo with input error."""

    def test_user_create_todo_list_no_workspace_exists_raises(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo, test_todolist_info: TestTodoListInfo) -> None:
        """Test that if the workspace does not exist, an error will be raised."""

        user1, access_token1 = login_user

        response = client.delete(
            "/api/workspace/todolist/todo/?username={}&workspace_default_name={}&todolist_id={}&todo_id={}".format(user1.username, test_workspace_info.workspace_default_name, 1, 1),
            headers={"Authorization": f"Bearer {access_token1}"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_json = response.json()
        assert response_json["error"] == "NotFoundError"
        assert response_json["error_msg"] == f'Workspace "{test_workspace_info.workspace_default_name}" not found.'
        assert response_json["msg"] is None
        assert response_json["data"] is None
    
    def test_user_create_todo_user_not_exists_raises(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo, test_todolist_info: TestTodoListInfo) -> None:
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
            "/api/workspace/todolist/todo/?username={}&workspace_default_name={}&todolist_id={}&todo_id={}".format(user_does_not_exist, test_workspace_info.workspace_default_name, 1, 1),
            headers={"Authorization": f"Bearer {leaky_access_token}"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_json = response.json()
        assert response_json["error"] == "NotFoundError"
        assert response_json["error_msg"] == f'User "{user_does_not_exist}" not found.'
        assert response_json["msg"] is None
        assert response_json["data"] is None
    
    def test_user_create_todo_user_not_joined_workspace_raises(self, client: TestClient, login_users: Tuple[Tuple[TestUserInfo, str], Tuple[TestUserInfo, str]], test_workspace_info: TestWorkspaceInfo, test_todolist_info: TestTodoListInfo) -> None:
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
            "/api/workspace/todolist/todo/?username={}&workspace_default_name={}&todolist_id={}&todo_id={}".format(user2.username, test_workspace_info.workspace_default_name, 1, 1),
            headers={"Authorization": f"Bearer {access_token2}"}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_json = response.json()
        assert response_json["error"] == "NotFoundError"
        assert response_json["error_msg"] == f'User "{user2.username}" has not joined workspace "{test_workspace_info.workspace_default_name}".'
        assert response_json["msg"] is None
        assert response_json["data"] is None
    
    def test_user_create_todo_no_todolist_raises(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo, test_todolist_info: TestTodoListInfo) -> None:
        """Test that if the todo list does not exist, an error will be raised."""
        
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

        invalid_todolist_id = int(create_todolist_response.json()["data"]) + 1
        
        response = client.delete(
            "/api/workspace/todolist/todo/?username={}&workspace_default_name={}&todolist_id={}&todo_id={}".format(user.username, test_workspace_info.workspace_default_name, invalid_todolist_id, 1),
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_json = response.json()
        assert response_json["error"] == "NotFoundError"
        assert response_json["error_msg"] == f'Todo list of id "{invalid_todolist_id}" is not found in workspace "{test_workspace_info.workspace_default_name}".'
        assert response_json["msg"] is None
        assert response_json["data"] is None
    
    def test_user_change_todo_no_todo_raises(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo, test_todolist_info: TestTodoListInfo) -> None:
        """Test that if the todo does not exist, an error will be raised."""
        
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

        create_todo_response = client.post(
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

        invalid_todo_id = int(create_todo_response.json()["data"]) + 1
        
        response = client.delete(
            "/api/workspace/todolist/todo/?username={}&workspace_default_name={}&todolist_id={}&todo_id={}".format(user.username, test_workspace_info.workspace_default_name, 1, invalid_todo_id),
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_json = response.json()
        assert response_json["error"] == "NotFoundError"
        assert response_json["error_msg"] == f'Todo of id "{invalid_todo_id}" is not found in todo list of id "{int(create_todolist_response.json()["data"])}" in workspace "{test_workspace_info.workspace_default_name}".'
        assert response_json["msg"] is None
        assert response_json["data"] is None
