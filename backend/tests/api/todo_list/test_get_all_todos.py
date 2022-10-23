from typing import Tuple
from fastapi import status
from fastapi.testclient import TestClient
from data_models import DatabaseConnection
from data_models.models import TodoList, WorkSpace
import pytest
import jwt # type: ignore
from config.auth_tokens_config import AUTH_TOKENS_CONFIG
import time
from ...mock_data import TestUserInfo, TestWorkspaceInfo, TestTodoListInfo

def create_token(username: str, exp_time: int) -> str:
    """Return an expired token"""
    
    return jwt.encode({"username": username, "exp": time.time() + exp_time}, AUTH_TOKENS_CONFIG.secret_key, algorithm=AUTH_TOKENS_CONFIG.algorithm)

class TestGetTodos:
    """Test the get todos endpoint."""

    def test_workspace_owner_get_all_todos(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo, test_todolist_info: TestTodoListInfo) -> None:
        """Test that a workspace owner can get all todos of a todo list in the workspace."""
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

        todolist_todo1_respnose = client.post(
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

        todolist_todo2_respnose = client.post(
            "/api/workspace/todolist/todo/",
            json = {
                "username": user.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_id": int(create_todolist_response.json()["data"]),
                "todo_name": "new_testing",
                "todo_description": "new_testing",
                "todo_due_date": "2021-01-02",
                "todo_status": "pending",
                "todo_priority": "low",
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        todolist_todo3_respnose = client.post(
            "/api/workspace/todolist/todo/",
            json = {
                "username": user.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_id": int(create_todolist_response.json()["data"]),
                "todo_name": "old_testing",
                "todo_description": "old_testing",
                "todo_due_date": "2023-01-02",
                "todo_status": "finished",
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        response = client.get(
            "/api/workspace/todolist/todos/?username={}&workspace_default_name={}&todolist_id={}".format(user.username, test_workspace_info.workspace_default_name, create_todolist_response.json()["data"]),
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        response_json = response.json()
        assert response_json["error"] is None
        assert response_json["error_msg"] is None
        assert len(response_json["data"]) == 3
        for todo in response_json["data"]:
            if todo["todo_id"] == int(todolist_todo1_respnose.json()["data"]):
                assert todo["todo_name"] == "testing"
                assert todo["todo_description"] == "testing"
                assert todo["todo_due_date"] == "2021-01-01 00:00:00"
                assert todo["todo_priority"] == "high"
                assert todo["todo_status"] == "created"
            elif todo["todo_id"] == int(todolist_todo2_respnose.json()["data"]):
                assert todo["todo_name"] == "new_testing"
                assert todo["todo_description"] == "new_testing"
                assert todo["todo_due_date"] == "2021-01-02 00:00:00"
                assert todo["todo_priority"] == "low"
                assert todo["todo_status"] == "pending"
            else:
                assert todo["todo_id"] == int(todolist_todo3_respnose.json()["data"])
                assert todo["todo_name"] == "old_testing"
                assert todo["todo_description"] == "old_testing"
                assert todo["todo_due_date"] == "2023-01-02 00:00:00"
                assert todo["todo_priority"] is None
                assert todo["todo_status"] == "finished"
        assert response_json["msg"] == f'Get all todos in todolist "{test_todolist_info.todolist_name}" in workspace "{test_workspace_info.workspace_default_name}" successfully.'

    def test_workspace_member_get_all_todos(self, client: TestClient, login_users: Tuple[Tuple[TestUserInfo, str], Tuple[TestUserInfo, str]], test_workspace_info: TestWorkspaceInfo, test_todolist_info: TestTodoListInfo) -> None:
        """Test that a workspace member can create a todolist in the workspace."""
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

        response = client.post(
            "/api/workspace/todolist/",
            json = {
                "username": user2.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_name": test_todolist_info.todolist_name,
            },
            headers={"Authorization": f"Bearer {access_token2}"}
        )

        create_todolist_response = client.post(
            "/api/workspace/todolist/",
            json = {
                "username": user1.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_name": test_todolist_info.todolist_name,
            },
            headers={"Authorization": f"Bearer {access_token1}"}
        )

        todolist_todo1_respnose = client.post(
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

        todolist_todo2_respnose = client.post(
            "/api/workspace/todolist/todo/",
            json = {
                "username": user1.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_id": int(create_todolist_response.json()["data"]),
                "todo_name": "new_testing",
                "todo_description": "new_testing",
                "todo_due_date": "2021-01-02",
                "todo_status": "pending",
                "todo_priority": "low",
            },
            headers={"Authorization": f"Bearer {access_token1}"}
        )

        todolist_todo3_respnose = client.post(
            "/api/workspace/todolist/todo/",
            json = {
                "username": user1.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_id": int(create_todolist_response.json()["data"]),
                "todo_name": "old_testing",
                "todo_description": "old_testing",
                "todo_due_date": "2023-01-02",
                "todo_status": "finished",
            },
            headers={"Authorization": f"Bearer {access_token1}"}
        )

        response = client.get(
            "/api/workspace/todolist/todos/?username={}&workspace_default_name={}&todolist_id={}".format(user2.username, test_workspace_info.workspace_default_name, create_todolist_response.json()["data"]),
            headers={"Authorization": f"Bearer {access_token2}"}
        )

        assert response.status_code == status.HTTP_200_OK
        response_json = response.json()
        assert response_json["error"] is None
        assert response_json["error_msg"] is None
        assert len(response_json["data"]) == 3
        for todo in response_json["data"]:
            if todo["todo_id"] == int(todolist_todo1_respnose.json()["data"]):
                assert todo["todo_name"] == "testing"
                assert todo["todo_description"] == "testing"
                assert todo["todo_due_date"] == "2021-01-01 00:00:00"
                assert todo["todo_priority"] == "high"
                assert todo["todo_status"] == "created"
            elif todo["todo_id"] == int(todolist_todo2_respnose.json()["data"]):
                assert todo["todo_name"] == "new_testing"
                assert todo["todo_description"] == "new_testing"
                assert todo["todo_due_date"] == "2021-01-02 00:00:00"
                assert todo["todo_priority"] == "low"
                assert todo["todo_status"] == "pending"
            else:
                assert todo["todo_id"] == int(todolist_todo3_respnose.json()["data"])
                assert todo["todo_name"] == "old_testing"
                assert todo["todo_description"] == "old_testing"
                assert todo["todo_due_date"] == "2023-01-02 00:00:00"
                assert todo["todo_priority"] is None
                assert todo["todo_status"] == "finished"
        assert response_json["msg"] == f'Get all todos in todolist "{test_todolist_info.todolist_name}" in workspace "{test_workspace_info.workspace_default_name}" successfully.'

    def test_empty_todolist_get_todos_return_nothing(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo, test_todolist_info: TestTodoListInfo) -> None:
        """Test when the todolist is empty, we can get nothing from the get function"""

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

        response = client.get(
            "/api/workspace/todolist/todos/?username={}&workspace_default_name={}&todolist_id={}".format(user.username, test_workspace_info.workspace_default_name, create_todolist_response.json()["data"]),
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        response_json = response.json()
        assert response_json["error"] is None
        assert response_json["error_msg"] is None
        assert response_json["data"] == []
        assert response_json["msg"] == f'Get all todos in todolist "{test_todolist_info.todolist_name}" in workspace "{test_workspace_info.workspace_default_name}" successfully.'

class TestGetTodosFilter:
    
    def test_workspace_owner_get_all_todos_filter_str(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo, test_todolist_info: TestTodoListInfo) -> None:
        """Test that a workspace member can get all todos of a todo list with filter of string fields in the workspace."""
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

        todolist_todo1_respnose = client.post(
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

        todolist_todo2_respnose = client.post(
            "/api/workspace/todolist/todo/",
            json = {
                "username": user.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_id": int(create_todolist_response.json()["data"]),
                "todo_name": "new_testing",
                "todo_description": "new_testing",
                "todo_due_date": "2021-01-02",
                "todo_status": "pending",
                "todo_priority": "low",
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        todolist_todo3_respnose = client.post(
            "/api/workspace/todolist/todo/",
            json = {
                "username": user.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_id": int(create_todolist_response.json()["data"]),
                "todo_name": "old_testing",
                "todo_description": "old_testing",
                "todo_due_date": "2023-01-02",
                "todo_status": "finished",
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        response = client.get(
            "/api/workspace/todolist/todos/?username={}&workspace_default_name={}&todolist_id={}&name={}".format(user.username, test_workspace_info.workspace_default_name, create_todolist_response.json()["data"], "[eq]testing"),
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        response_json = response.json()
        assert response_json["error"] is None
        assert response_json["error_msg"] is None
        assert len(response_json["data"]) == 1
        todo = response_json["data"][0]
        assert todo["todo_name"] == "testing"
        assert todo["todo_description"] == "testing"
        assert todo["todo_due_date"] == "2021-01-01 00:00:00"
        assert todo["todo_priority"] == "high"
        assert todo["todo_status"] == "created"
        assert response_json["msg"] == f'Get all todos in todolist "{test_todolist_info.todolist_name}" in workspace "{test_workspace_info.workspace_default_name}" successfully.'

        response = client.get(
            "/api/workspace/todolist/todos/?username={}&workspace_default_name={}&todolist_id={}&status={}".format(user.username, test_workspace_info.workspace_default_name, create_todolist_response.json()["data"], "[ne]pending"),
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        response_json = response.json()
        assert response_json["error"] is None
        assert response_json["error_msg"] is None
        assert len(response_json["data"]) == 2
        for todo in response_json["data"]:
            if todo["todo_id"] == int(todolist_todo1_respnose.json()["data"]):
                assert todo["todo_name"] == "testing"
                assert todo["todo_description"] == "testing"
                assert todo["todo_due_date"] == "2021-01-01 00:00:00"
                assert todo["todo_priority"] == "high"
                assert todo["todo_status"] == "created"
            else:
                assert todo["todo_id"] == int(todolist_todo3_respnose.json()["data"])
                assert todo["todo_name"] == "old_testing"
                assert todo["todo_description"] == "old_testing"
                assert todo["todo_due_date"] == "2023-01-02 00:00:00"
                assert todo["todo_priority"] is None
                assert todo["todo_status"] == "finished"
        assert response_json["msg"] == f'Get all todos in todolist "{test_todolist_info.todolist_name}" in workspace "{test_workspace_info.workspace_default_name}" successfully.'

        response = client.get(
            "/api/workspace/todolist/todos/?username={}&workspace_default_name={}&todolist_id={}&priority={}".format(user.username, test_workspace_info.workspace_default_name, create_todolist_response.json()["data"], "[eq]NULL"),
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        response_json = response.json()
        assert response_json["error"] is None
        assert response_json["error_msg"] is None
        assert len(response_json["data"]) == 1
        todo = response_json["data"][0]

        assert todo["todo_name"] == "old_testing"
        assert todo["todo_description"] == "old_testing"
        assert todo["todo_due_date"] == "2023-01-02 00:00:00"
        assert todo["todo_priority"] is None
        assert todo["todo_status"] == "finished"
        assert response_json["msg"] == f'Get all todos in todolist "{test_todolist_info.todolist_name}" in workspace "{test_workspace_info.workspace_default_name}" successfully.'
    
    def test_workspace_owner_get_all_todos_filter_datetime(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo, test_todolist_info: TestTodoListInfo) -> None:
        """Test that a workspace owner can get all todos of a todo list with filter of datetime fields in the workspace."""
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

        todolist_todo1_respnose = client.post(
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

        todolist_todo2_respnose = client.post(
            "/api/workspace/todolist/todo/",
            json = {
                "username": user.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_id": int(create_todolist_response.json()["data"]),
                "todo_name": "new_testing",
                "todo_description": "new_testing",
                "todo_due_date": "2021-01-02",
                "todo_status": "pending",
                "todo_priority": "low",
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        todolist_todo3_respnose = client.post(
            "/api/workspace/todolist/todo/",
            json = {
                "username": user.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_id": int(create_todolist_response.json()["data"]),
                "todo_name": "old_testing",
                "todo_description": "old_testing",
                "todo_due_date": "2023-01-02",
                "todo_status": "finished",
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        response = client.get(
            "/api/workspace/todolist/todos/?username={}&workspace_default_name={}&todolist_id={}&due_date={}".format(user.username, test_workspace_info.workspace_default_name, create_todolist_response.json()["data"], "[ge]2019-01-01"),
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        response_json = response.json()
        assert response_json["error"] is None
        assert response_json["error_msg"] is None
        assert len(response_json["data"]) == 3
        for todo in response_json["data"]:
            if todo["todo_id"] == int(todolist_todo1_respnose.json()["data"]):
                assert todo["todo_name"] == "testing"
                assert todo["todo_description"] == "testing"
                assert todo["todo_due_date"] == "2021-01-01 00:00:00"
                assert todo["todo_priority"] == "high"
                assert todo["todo_status"] == "created"
            elif todo["todo_id"] == int(todolist_todo2_respnose.json()["data"]):
                assert todo["todo_name"] == "new_testing"
                assert todo["todo_description"] == "new_testing"
                assert todo["todo_due_date"] == "2021-01-02 00:00:00"
                assert todo["todo_priority"] == "low"
                assert todo["todo_status"] == "pending"
            else:
                assert todo["todo_id"] == int(todolist_todo3_respnose.json()["data"])
                assert todo["todo_name"] == "old_testing"
                assert todo["todo_description"] == "old_testing"
                assert todo["todo_due_date"] == "2023-01-02 00:00:00"
                assert todo["todo_priority"] is None
                assert todo["todo_status"] == "finished"
        assert response_json["msg"] == f'Get all todos in todolist "{test_todolist_info.todolist_name}" in workspace "{test_workspace_info.workspace_default_name}" successfully.'

        response = client.get(
            "/api/workspace/todolist/todos/?username={}&workspace_default_name={}&todolist_id={}&due_date={}".format(user.username, test_workspace_info.workspace_default_name, create_todolist_response.json()["data"], "[le]2023-01-01"),
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        response_json = response.json()
        assert response_json["error"] is None
        assert response_json["error_msg"] is None
        assert len(response_json["data"]) == 2
        for todo in response_json["data"]:
            if todo["todo_id"] == int(todolist_todo1_respnose.json()["data"]):
                assert todo["todo_name"] == "testing"
                assert todo["todo_description"] == "testing"
                assert todo["todo_due_date"] == "2021-01-01 00:00:00"
                assert todo["todo_priority"] == "high"
                assert todo["todo_status"] == "created"
            else:
                assert todo["todo_id"] == int(todolist_todo2_respnose.json()["data"])
                assert todo["todo_name"] == "new_testing"
                assert todo["todo_description"] == "new_testing"
                assert todo["todo_due_date"] == "2021-01-02 00:00:00"
                assert todo["todo_priority"] == "low"
                assert todo["todo_status"] == "pending"
        assert response_json["msg"] == f'Get all todos in todolist "{test_todolist_info.todolist_name}" in workspace "{test_workspace_info.workspace_default_name}" successfully.'

        response = client.get(
            "/api/workspace/todolist/todos/?username={}&workspace_default_name={}&todolist_id={}&due_date={}".format(user.username, test_workspace_info.workspace_default_name, create_todolist_response.json()["data"], "[ne]2021-01-02"),
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        response_json = response.json()
        assert response_json["error"] is None
        assert response_json["error_msg"] is None
        assert len(response_json["data"]) == 2
        for todo in response_json["data"]:
            if todo["todo_id"] == int(todolist_todo1_respnose.json()["data"]):
                assert todo["todo_name"] == "testing"
                assert todo["todo_description"] == "testing"
                assert todo["todo_due_date"] == "2021-01-01 00:00:00"
                assert todo["todo_priority"] == "high"
                assert todo["todo_status"] == "created"
            else:
                assert todo["todo_id"] == int(todolist_todo3_respnose.json()["data"])
                assert todo["todo_name"] == "old_testing"
                assert todo["todo_description"] == "old_testing"
                assert todo["todo_due_date"] == "2023-01-02 00:00:00"
                assert todo["todo_priority"] is None
                assert todo["todo_status"] == "finished"
        assert response_json["msg"] == f'Get all todos in todolist "{test_todolist_info.todolist_name}" in workspace "{test_workspace_info.workspace_default_name}" successfully.'

        response = client.get(
            "/api/workspace/todolist/todos/?username={}&workspace_default_name={}&todolist_id={}&due_date={}".format(user.username, test_workspace_info.workspace_default_name, create_todolist_response.json()["data"], "[lt]2021-01-02 00:00:00"),
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        response_json = response.json()
        assert response_json["error"] is None
        assert response_json["error_msg"] is None
        assert len(response_json["data"]) == 1
        todo = response_json["data"][0]
        assert todo["todo_name"] == "testing"
        assert todo["todo_description"] == "testing"
        assert todo["todo_due_date"] == "2021-01-01 00:00:00"
        assert todo["todo_priority"] == "high"
        assert todo["todo_status"] == "created"
        assert response_json["msg"] == f'Get all todos in todolist "{test_todolist_info.todolist_name}" in workspace "{test_workspace_info.workspace_default_name}" successfully.'

class TestGetTodosSort:
    
    def test_workspace_owner_get_all_todos_sort(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo, test_todolist_info: TestTodoListInfo) -> None:
        """Test that a workspace member can get all todos of a todo list with filter of string fields in the workspace."""
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

        client.post(
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

        client.post(
            "/api/workspace/todolist/todo/",
            json = {
                "username": user.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_id": int(create_todolist_response.json()["data"]),
                "todo_name": "new_testing",
                "todo_description": "new_testing",
                "todo_due_date": "2021-01-02",
                "todo_status": "pending",
                "todo_priority": "low",
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        client.post(
            "/api/workspace/todolist/todo/",
            json = {
                "username": user.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_id": int(create_todolist_response.json()["data"]),
                "todo_name": "old_testing",
                "todo_description": "old_testing",
                "todo_due_date": "2023-01-02",
                "todo_status": "finished",
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        response = client.get(
            "/api/workspace/todolist/todos/?username={}&workspace_default_name={}&todolist_id={}&sort_by={}&order_by={}".format(user.username, test_workspace_info.workspace_default_name, create_todolist_response.json()["data"], "name", "asc"),
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        response_json = response.json()
        assert response_json["error"] is None
        assert response_json["error_msg"] is None
        assert len(response_json["data"]) == 3
        first_todo = response_json["data"][0]
        assert first_todo["todo_name"] == "new_testing"
        assert first_todo["todo_description"] == "new_testing"
        assert first_todo["todo_due_date"] == "2021-01-02 00:00:00"
        assert first_todo["todo_priority"] == "low"
        second_todo = response_json["data"][1]
        assert second_todo["todo_name"] == "old_testing"
        assert second_todo["todo_description"] == "old_testing"
        assert second_todo["todo_due_date"] == "2023-01-02 00:00:00"
        assert second_todo["todo_priority"] is None
        assert second_todo["todo_status"] == "finished"
        third_todo = response_json["data"][2]
        assert third_todo["todo_name"] == "testing"
        assert third_todo["todo_description"] == "testing"
        assert third_todo["todo_due_date"] == "2021-01-01 00:00:00"
        assert third_todo["todo_priority"] == "high"
        assert third_todo["todo_status"] == "created"
        assert response_json["msg"] == f'Get all todos in todolist "{test_todolist_info.todolist_name}" in workspace "{test_workspace_info.workspace_default_name}" successfully.'

        response = client.get(
            "/api/workspace/todolist/todos/?username={}&workspace_default_name={}&todolist_id={}&sort_by={}&order_by={}".format(user.username, test_workspace_info.workspace_default_name, create_todolist_response.json()["data"], "status", "desc"),
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        response_json = response.json()
        assert response_json["error"] is None
        assert response_json["error_msg"] is None
        assert len(response_json["data"]) == 3
        first_todo = response_json["data"][0]
        assert first_todo["todo_name"] == "new_testing"
        assert first_todo["todo_description"] == "new_testing"
        assert first_todo["todo_due_date"] == "2021-01-02 00:00:00"
        assert first_todo["todo_priority"] == "low"
        assert first_todo["todo_status"] == "pending"
        second_todo = response_json["data"][1]
        assert second_todo["todo_name"] == "old_testing"
        assert second_todo["todo_description"] == "old_testing"
        assert second_todo["todo_due_date"] == "2023-01-02 00:00:00"
        assert second_todo["todo_priority"] is None
        assert second_todo["todo_status"] == "finished"
        third_todo = response_json["data"][2]
        assert third_todo["todo_name"] == "testing"
        assert third_todo["todo_description"] == "testing"
        assert third_todo["todo_due_date"] == "2021-01-01 00:00:00"
        assert third_todo["todo_priority"] == "high"
        assert third_todo["todo_status"] == "created"
        assert response_json["msg"] == f'Get all todos in todolist "{test_todolist_info.todolist_name}" in workspace "{test_workspace_info.workspace_default_name}" successfully.'

        response = client.get(
            "/api/workspace/todolist/todos/?username={}&workspace_default_name={}&todolist_id={}&sort_by={}".format(user.username, test_workspace_info.workspace_default_name, create_todolist_response.json()["data"], "due_date"),
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        response_json = response.json()
        assert response_json["error"] is None
        assert response_json["error_msg"] is None
        assert len(response_json["data"]) == 3
        first_todo = response_json["data"][0]
        assert first_todo["todo_name"] == "testing"
        assert first_todo["todo_description"] == "testing"
        assert first_todo["todo_due_date"] == "2021-01-01 00:00:00"
        assert first_todo["todo_priority"] == "high"
        assert first_todo["todo_status"] == "created"
        second_todo = response_json["data"][1]
        assert second_todo["todo_name"] == "new_testing"
        assert second_todo["todo_description"] == "new_testing"
        assert second_todo["todo_due_date"] == "2021-01-02 00:00:00"
        assert second_todo["todo_priority"] == "low"
        assert second_todo["todo_status"] == "pending"
        third_todo = response_json["data"][2]
        assert third_todo["todo_name"] == "old_testing"
        assert third_todo["todo_description"] == "old_testing"
        assert third_todo["todo_due_date"] == "2023-01-02 00:00:00"
        assert third_todo["todo_priority"] is None
        assert third_todo["todo_status"] == "finished"
        assert response_json["msg"] == f'Get all todos in todolist "{test_todolist_info.todolist_name}" in workspace "{test_workspace_info.workspace_default_name}" successfully.'
    
    def test_workspace_owner_get_all_todos_sort_with_filter(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo, test_todolist_info: TestTodoListInfo) -> None:
        """Test that a workspace owner can get all todos of a todo list with filter of datetime fields in the workspace."""
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

        todolist_todo1_respnose = client.post(
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

        todolist_todo2_respnose = client.post(
            "/api/workspace/todolist/todo/",
            json = {
                "username": user.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_id": int(create_todolist_response.json()["data"]),
                "todo_name": "new_testing",
                "todo_description": "new_testing",
                "todo_due_date": "2021-01-02",
                "todo_status": "pending",
                "todo_priority": "low",
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        todolist_todo3_respnose = client.post(
            "/api/workspace/todolist/todo/",
            json = {
                "username": user.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_id": int(create_todolist_response.json()["data"]),
                "todo_name": "old_testing",
                "todo_description": "old_testing",
                "todo_due_date": "2023-01-02",
                "todo_status": "finished",
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        response = client.get(
            "/api/workspace/todolist/todos/?username={}&workspace_default_name={}&todolist_id={}&due_date={}&sort_by={}&order_by={}".format(user.username, test_workspace_info.workspace_default_name, create_todolist_response.json()["data"], "[lt]2022-01-01", "description", "desc"),
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        response_json = response.json()
        assert response_json["error"] is None
        assert response_json["error_msg"] is None
        assert len(response_json["data"]) == 2
        first_todo = response_json["data"][0]
        assert first_todo["todo_name"] == "testing"
        assert first_todo["todo_description"] == "testing"
        assert first_todo["todo_due_date"] == "2021-01-01 00:00:00"
        assert first_todo["todo_priority"] == "high"
        assert first_todo["todo_status"] == "created"
        second_todo = response_json["data"][1]
        assert second_todo["todo_name"] == "new_testing"
        assert second_todo["todo_description"] == "new_testing"
        assert second_todo["todo_due_date"] == "2021-01-02 00:00:00"
        assert second_todo["todo_priority"] == "low"
        assert second_todo["todo_status"] == "pending"
        assert response_json["msg"] == f'Get all todos in todolist "{test_todolist_info.todolist_name}" in workspace "{test_workspace_info.workspace_default_name}" successfully.'

        response = client.get(
            "/api/workspace/todolist/todos/?username={}&workspace_default_name={}&todolist_id={}&due_date={}&name={}&sort_by={}".format(user.username, test_workspace_info.workspace_default_name, create_todolist_response.json()["data"], "[le]2023-01-01", "[ne]testing", "due_date"),
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        response_json = response.json()
        assert response_json["error"] is None
        assert response_json["error_msg"] is None
        assert len(response_json["data"]) == 1
        first_todo = response_json["data"][0]
        assert first_todo["todo_name"] == "new_testing"
        assert first_todo["todo_description"] == "new_testing"
        assert first_todo["todo_due_date"] == "2021-01-02 00:00:00"
        assert first_todo["todo_priority"] == "low"
        assert first_todo["todo_status"] == "pending"
        assert response_json["msg"] == f'Get all todos in todolist "{test_todolist_info.todolist_name}" in workspace "{test_workspace_info.workspace_default_name}" successfully.'

class TestGetTodosFilterSortingWrongFormatError:
    """Test the get todos with filter and sorting but wrong format"""

    def test_filter_no_specifier(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo, test_todolist_info: TestTodoListInfo) -> None:
        """Test that error occurs when there is no comparison specifier of the filter query."""
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

        response = client.get(
            "/api/workspace/todolist/todos/?username={}&workspace_default_name={}&todolist_id={}&name={}".format(user.username, test_workspace_info.workspace_default_name, create_todolist_response.json()["data"], "testing"),
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        response_json = response.json()
        assert response_json["error"] == "ValidationError"
        assert "1 validation error for Request" in response_json["error_msg"]
        assert response_json["data"] is None
        assert response_json["msg"] is None
    
    def test_filter_wrong_specifier(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo, test_todolist_info: TestTodoListInfo) -> None:
        """Test that error occurs when the comparison specifier of the filter query is wrong."""
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

        response = client.get(
            "/api/workspace/todolist/todos/?username={}&workspace_default_name={}&todolist_id={}&name={}".format(user.username, test_workspace_info.workspace_default_name, create_todolist_response.json()["data"], "[ab]testing"),
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        response_json = response.json()
        assert response_json["error"] == "ValidationError"
        assert "1 validation error for Request" in response_json["error_msg"]
        assert response_json["data"] is None
        assert response_json["msg"] is None
    
    def test_sort_wrong_field(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo, test_todolist_info: TestTodoListInfo) -> None:
        """Test that error occurs when the sorting field of the filter query is wrong."""
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

        response = client.get(
            "/api/workspace/todolist/todos/?username={}&workspace_default_name={}&todolist_id={}&sort_by={}".format(user.username, test_workspace_info.workspace_default_name, create_todolist_response.json()["data"], "hello_world!"),
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        response_json = response.json()
        assert response_json["error"] == "ValidationError"
        assert "1 validation error for Request" in response_json["error_msg"]
        assert response_json["data"] is None
        assert response_json["msg"] is None
class TestCreateTodoListTokenError:
    """Test the create todolist with token error."""

    def test_create_todo_list_no_access_token_raises(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo, test_todolist_info: TestTodoListInfo) -> None:
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

        response = client.get(
            "/api/workspace/todolist/todos/?username={}&workspace_default_name={}&todolist_id={}".format(user.username, test_workspace_info.workspace_default_name, create_todolist_response.json()["data"]),
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

        response = client.get(
            "/api/workspace/todolist/todos/?username={}&workspace_default_name={}&todolist_id={}".format(user.username, test_workspace_info.workspace_default_name, create_todolist_response.json()["data"]),
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

        response = client.get(
            "/api/workspace/todolist/todos/?username={}&workspace_default_name={}&todolist_id={}".format(user.username, test_workspace_info.workspace_default_name, create_todolist_response.json()["data"]),
            headers={"Authorization": f"Bearer {expired_access_token}"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        response_json = response.json()
        assert response_json["error"] == "TokenExpiredError"
        assert response_json["error_msg"] == "Token has expired."
        assert response_json["data"] is None
        assert response_json["msg"] is None
class TestUserGetTodosInputError:
    """Test the user create todo list with input error."""

    def test_user_get_todos_no_workspace_exists_raises(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo, test_todolist_info: TestTodoListInfo) -> None:
        """Test that if the workspace does not exist, an error will be raised."""

        user, access_token = login_user


        response = client.get(
            "/api/workspace/todolist/todos/?username={}&workspace_default_name={}&todolist_id={}".format(user.username, test_workspace_info.workspace_default_name, 1),
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_json = response.json()
        assert response_json["error"] == "NotFoundError"
        assert response_json["error_msg"] == f'Workspace "{test_workspace_info.workspace_default_name}" not found.'
        assert response_json["msg"] is None
        assert response_json["data"] is None
    
    def test_user_get_todos_user_not_exists_raises(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo, test_todolist_info: TestTodoListInfo) -> None:
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

        response = client.get(
            "/api/workspace/todolist/todos/?username={}&workspace_default_name={}&todolist_id={}".format(user_does_not_exist, test_workspace_info.workspace_default_name, 1),
            headers={"Authorization": f"Bearer {leaky_access_token}"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_json = response.json()
        assert response_json["error"] == "NotFoundError"
        assert response_json["error_msg"] == f'User "{user_does_not_exist}" not found.'
        assert response_json["msg"] is None
        assert response_json["data"] is None
    
    def test_user_get_todos_user_not_joined_workspace_raises(self, client: TestClient, login_users: Tuple[Tuple[TestUserInfo, str], Tuple[TestUserInfo, str]], test_workspace_info: TestWorkspaceInfo, test_todolist_info: TestTodoListInfo) -> None:
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

        create_todolist_response = client.post(
            "/api/workspace/todolist/",
            json = {
                "username": user1.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_name": test_todolist_info.todolist_name,
            },
            headers={"Authorization": f"Bearer {access_token1}"}
        )

        response = client.get(
            "/api/workspace/todolist/todos/?username={}&workspace_default_name={}&todolist_id={}".format(user2.username, test_workspace_info.workspace_default_name, create_todolist_response.json()["data"]),
            headers={"Authorization": f"Bearer {access_token2}"}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_json = response.json()
        assert response_json["error"] == "NotFoundError"
        assert response_json["error_msg"] == f'User "{user2.username}" has not joined workspace "{test_workspace_info.workspace_default_name}".'
        assert response_json["msg"] is None
        assert response_json["data"] is None

    def test_user_get_todos_no_todolist_raises(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo, test_todolist_info: TestTodoListInfo) -> None:
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


        response = client.get(
            "/api/workspace/todolist/todos/?username={}&workspace_default_name={}&todolist_id={}".format(user.username, test_workspace_info.workspace_default_name, invalid_todolist_id),
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_json = response.json()
        assert response_json["error"] == "NotFoundError"
        assert response_json["error_msg"] == f'Todo list of id "{invalid_todolist_id}" is not found in workspace "{test_workspace_info.workspace_default_name}".'
        assert response_json["msg"] is None
        assert response_json["data"] is None