import time
from typing import Tuple
from fastapi import status
from fastapi.testclient import TestClient
import jwt # type: ignore
from config.auth_tokens_config import AUTH_TOKENS_CONFIG
from data_models import DatabaseConnection
from data_models.models import WorkSpace
from typing import Tuple
from ...mock_data import TestUserInfo, TestWorkspaceInfo, TestTodoListInfo

def create_token(username: str, exp_time: int) -> str:
    """Return an expired token"""
    
    return jwt.encode({"username": username, "exp": time.time() + exp_time}, AUTH_TOKENS_CONFIG.secret_key, algorithm=AUTH_TOKENS_CONFIG.algorithm)

class TestGetAllTodoListsTodos:
    """Test the create workspace."""

    def test_empty_workspace_get_no_info(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo) -> None:
        """Test that an empty workspace will return no info."""
        user, access_token = login_user

        client.post(
            "/api/workspace/",
            json = {
                "username": user.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,   
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        response = client.get(
            "/api/workspace/todolists/todos/?username={}&workspace_default_name={}".format(user.username, test_workspace_info.workspace_default_name),
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        response_json = response.json()
        assert response_json["error"] is None
        assert response_json["error_msg"] is None
        assert response_json["data"] == []
        assert response_json["msg"] == f'Get all todolists and corresponding todos in workspace "{test_workspace_info.workspace_default_name}" successfully.'
    
    def test_workspace_empty_todolists_get_todolists_info(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo, permuted_test_todolist_info: Tuple[TestTodoListInfo, TestTodoListInfo]):
        """Test that a workspace with empty todolists will return infos of todolists."""

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

        create_todolist1_response = client.post(
            "/api/workspace/todolist/",
            json = {
                "username": user.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_name": todolist_info1.todolist_name,
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        create_todolist2_response = client.post(
            "/api/workspace/todolist/",
            json = {
                "username": user.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_name": todolist_info2.todolist_name,
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        response = client.get(
            "/api/workspace/todolists/todos/?username={}&workspace_default_name={}".format(user.username, test_workspace_info.workspace_default_name),
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        response_json = response.json()
        assert response_json["error"] is None
        assert response_json["error_msg"] is None
        assert len(response_json["data"]) == 2
        for todolist in response_json["data"]:
            if todolist["todolist_id"] == int(create_todolist1_response.json()["data"]):
                assert todolist["todolist_name"] == todolist_info1.todolist_name
                assert todolist["todos"] == []
            else:
                assert todolist["todolist_id"] == int(create_todolist2_response.json()["data"])
                assert todolist["todolist_name"] == todolist_info2.todolist_name
                assert todolist["todos"] == []
        assert response_json["msg"] == f'Get all todolists and corresponding todos in workspace "{test_workspace_info.workspace_default_name}" successfully.'


    def test_workspace_owner_get_alL_info(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo, permuted_test_todolist_info: Tuple[TestTodoListInfo, TestTodoListInfo]) -> None:
        """Test that a workspace owner can get all todos and todolists."""
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

        create_todolist1_response = client.post(
            "/api/workspace/todolist/",
            json = {
                "username": user.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_name": todolist_info1.todolist_name,
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        todolist1_todo1_respnose = client.post(
            "/api/workspace/todolist/todo/",
            json = {
                "username": user.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_id": int(create_todolist1_response.json()["data"]),
                "todo_name": "testing",
                "todo_description": "testing",
                "todo_due_date": "2021-01-01",
                "todo_status": "created",
                "todo_priority": "high",
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        todolist1_todo2_respnose = client.post(
            "/api/workspace/todolist/todo/",
            json = {
                "username": user.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_id": int(create_todolist1_response.json()["data"]),
                "todo_name": "new_testing",
                "todo_description": "new_testing",
                "todo_due_date": "2021-01-02",
                "todo_status": "pending",
                "todo_priority": "low",
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        todolist1_todo3_respnose = client.post(
            "/api/workspace/todolist/todo/",
            json = {
                "username": user.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_id": int(create_todolist1_response.json()["data"]),
                "todo_name": "old_testing",
                "todo_description": "old_testing",
                "todo_due_date": "2023-01-02",
                "todo_status": "finished",
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        create_todolist2_response = client.post(
            "/api/workspace/todolist/",
            json = {
                "username": user.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_name": todolist_info2.todolist_name,
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        todolist2_todo1_respnose = client.post(
            "/api/workspace/todolist/todo/",
            json = {
                "username": user.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_id": int(create_todolist2_response.json()["data"]),
                "todo_name": "testing_dev",
                "todo_description": "development",
                "todo_due_date": "2022-01-02",
                "todo_status": "started",
                "todo_priority": "medium",
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        response = client.get(
            "/api/workspace/todolists/todos/?username={}&workspace_default_name={}".format(user.username, test_workspace_info.workspace_default_name),
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        response_json = response.json()
        assert response_json["error"] is None
        assert response_json["error_msg"] is None
        assert len(response_json["data"]) == 2
        for todolist in response_json["data"]:
            if todolist["todolist_id"] == int(create_todolist1_response.json()["data"]) :
                assert len(todolist["todos"]) == 3
                assert todolist["todolist_name"] == todolist_info1.todolist_name
                for todo in todolist["todos"]:
                    if todo["todo_id"] == int(todolist1_todo1_respnose.json()["data"]):
                        assert todo["todo_name"] == "testing"
                        assert todo["todo_description"] == "testing"
                        assert todo["todo_due_date"] == "2021-01-01 00:00:00"
                        assert todo["todo_priority"] == "high"
                        assert todo["todo_status"] == "created"
                    elif todo["todo_id"] == int(todolist1_todo2_respnose.json()["data"]):
                        assert todo["todo_name"] == "new_testing"
                        assert todo["todo_description"] == "new_testing"
                        assert todo["todo_due_date"] == "2021-01-02 00:00:00"
                        assert todo["todo_priority"] == "low"
                        assert todo["todo_status"] == "pending"
                    else:
                        assert todo["todo_id"] == int(todolist1_todo3_respnose.json()["data"])
                        assert todo["todo_name"] == "old_testing"
                        assert todo["todo_description"] == "old_testing"
                        assert todo["todo_due_date"] == "2023-01-02 00:00:00"
                        assert todo["todo_priority"] is None
                        assert todo["todo_status"] == "finished"
            else:
                assert len(todolist["todos"]) == 1
                assert todolist["todolist_id"] == int(create_todolist2_response.json()["data"])
                assert todolist["todolist_name"] == todolist_info2.todolist_name
                for todo in todolist["todos"]:
                    assert todo["todo_id"] == int(todolist2_todo1_respnose.json()["data"])
                    assert todo["todo_name"] == "testing_dev"
                    assert todo["todo_description"] == "development"
                    assert todo["todo_due_date"] == "2022-01-02 00:00:00"
                    assert todo["todo_priority"] == "medium"
                    assert todo["todo_status"] == "started"
            
        assert response_json["msg"] == f'Get all todolists and corresponding todos in workspace "{test_workspace_info.workspace_default_name}" successfully.'
    
    def test_workspace_member_get_alL_info(self, client: TestClient, login_users: Tuple[Tuple[TestUserInfo, str], Tuple[TestUserInfo, str]], test_workspace_info: TestWorkspaceInfo, permuted_test_todolist_info: Tuple[TestTodoListInfo, TestTodoListInfo]) -> None:
        """Test that a workspace member can get all todos and todolists."""

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
        
        create_todolist1_response = client.post(
            "/api/workspace/todolist/",
            json = {
                "username": user2.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_name": todolist_info1.todolist_name,
            },
            headers={"Authorization": f"Bearer {access_token2}"}
        )

        todolist1_todo1_respnose = client.post(
            "/api/workspace/todolist/todo/",
            json = {
                "username": user2.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_id": int(create_todolist1_response.json()["data"]),
                "todo_name": "testing",
                "todo_description": "testing",
                "todo_due_date": "2021-01-01",
                "todo_status": "created",
                "todo_priority": "high",
            },
            headers={"Authorization": f"Bearer {access_token2}"}
        )

        todolist1_todo2_respnose = client.post(
            "/api/workspace/todolist/todo/",
            json = {
                "username": user2.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_id": int(create_todolist1_response.json()["data"]),
                "todo_name": "new_testing",
                "todo_description": "new_testing",
                "todo_due_date": "2021-01-02",
                "todo_status": "pending",
                "todo_priority": "low",
            },
            headers={"Authorization": f"Bearer {access_token2}"}
        )

        todolist1_todo3_respnose = client.post(
            "/api/workspace/todolist/todo/",
            json = {
                "username": user2.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_id": int(create_todolist1_response.json()["data"]),
                "todo_name": "old_testing",
                "todo_description": "old_testing",
                "todo_due_date": "2023-01-02",
                "todo_status": "finished",
            },
            headers={"Authorization": f"Bearer {access_token2}"}
        )

        create_todolist2_response = client.post(
            "/api/workspace/todolist/",
            json = {
                "username": user2.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_name": todolist_info2.todolist_name,
            },
            headers={"Authorization": f"Bearer {access_token2}"}
        )

        todolist2_todo1_respnose = client.post(
            "/api/workspace/todolist/todo/",
            json = {
                "username": user2.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
                "todolist_id": int(create_todolist2_response.json()["data"]),
                "todo_name": "testing_dev",
                "todo_description": "development",
                "todo_due_date": "2022-01-02",
                "todo_status": "started",
                "todo_priority": "medium",
            },
            headers={"Authorization": f"Bearer {access_token2}"}
        )

        response = client.get(
            "/api/workspace/todolists/todos/?username={}&workspace_default_name={}".format(user2.username, test_workspace_info.workspace_default_name),
            headers={"Authorization": f"Bearer {access_token2}"}
        )

        assert response.status_code == status.HTTP_200_OK
        response_json = response.json()
        assert response_json["error"] is None
        assert response_json["error_msg"] is None
        assert len(response_json["data"]) == 2
        for todolist in response_json["data"]:
            if todolist["todolist_id"] == int(create_todolist1_response.json()["data"]) :
                assert len(todolist["todos"]) == 3
                assert todolist["todolist_name"] == todolist_info1.todolist_name
                for todo in todolist["todos"]:
                    if todo["todo_id"] == int(todolist1_todo1_respnose.json()["data"]):
                        assert todo["todo_name"] == "testing"
                        assert todo["todo_description"] == "testing"
                        assert todo["todo_due_date"] == "2021-01-01 00:00:00"
                        assert todo["todo_priority"] == "high"
                        assert todo["todo_status"] == "created"
                    elif todo["todo_id"] == int(todolist1_todo2_respnose.json()["data"]):
                        assert todo["todo_name"] == "new_testing"
                        assert todo["todo_description"] == "new_testing"
                        assert todo["todo_due_date"] == "2021-01-02 00:00:00"
                        assert todo["todo_priority"] == "low"
                        assert todo["todo_status"] == "pending"
                    else:
                        assert todo["todo_name"] == "old_testing"
                        assert todo["todo_description"] == "old_testing"
                        assert todo["todo_due_date"] == "2023-01-02 00:00:00"
                        assert todo["todo_priority"] is None
                        assert todo["todo_status"] == "finished"
            else:
                assert todolist["todolist_name"] == todolist_info2.todolist_name
                assert len(todolist["todos"]) == 1
                for todo in todolist["todos"]:
                    assert todo["todo_id"] == int(todolist2_todo1_respnose.json()["data"])
                    assert todo["todo_name"] == "testing_dev"
                    assert todo["todo_description"] == "development"
                    assert todo["todo_due_date"] == "2022-01-02 00:00:00"
                    assert todo["todo_priority"] == "medium"
                    assert todo["todo_status"] == "started"

        assert response_json["msg"] == f'Get all todolists and corresponding todos in workspace "{test_workspace_info.workspace_default_name}" successfully.'
class TestGetTodoListsTodosTokenError:
    """Test getting todo lists and todos with token error."""

    def test_get_todolists_todos_no_access_token_raises(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo) -> None:
        """Test that todolists and todos cannot be get without access token."""
        
        user, access_token = login_user
        client.post(
            "/api/workspace/",
            json = {
                "username": user.username,
                "workspace_default_name": test_workspace_info.workspace_default_name,
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )

        response = client.get(
            "/api/workspace/todolists/todos/?username={}&workspace_default_name={}".format(user.username, test_workspace_info.workspace_default_name),
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        response_json = response.json()
        assert response_json["error"] == "UnauthorizedError"
        assert response_json["error_msg"] == "Unauthorized action."
        assert response_json["data"] is None
        assert response_json["msg"] is None
    
    def test_create_workspace_wrong_access_token_raises(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo) -> None:
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

        response = client.get(
            "/api/workspace/todolists/todos/?username={}&workspace_default_name={}".format(user.username, test_workspace_info.workspace_default_name),
            headers={"Authorization": f"Bearer {access_token}1"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        response_json = response.json()
        assert response_json["error"] == "InvalidTokenError"
        assert response_json["error_msg"] == "Invalid token."
        assert response_json["data"] is None
        assert response_json["msg"] is None
    
    def test_create_workspace_expired_access_token_raises(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo) -> None:
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

        response = client.get(
            "/api/workspace/todolists/todos/?username={}&workspace_default_name={}".format(user.username, test_workspace_info.workspace_default_name),
            headers={"Authorization": f"Bearer {expired_access_token}"}
        )


        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        response_json = response.json()
        assert response_json["error"] == "TokenExpiredError"
        assert response_json["error_msg"] == "Token has expired."
        assert response_json["data"] is None
        assert response_json["msg"] is None

class TestGetTodoListsTodosInputError:
    """Test getting todo lists and todos with input error."""

    def test_get_todolists_todos_user_not_exists_raises(self, client: TestClient, login_user: Tuple[TestUserInfo, str], test_workspace_info: TestWorkspaceInfo) -> None:
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
            "/api/workspace/todolists/todos/?username={}&workspace_default_name={}".format(user_does_not_exist, test_workspace_info.workspace_default_name),
            headers={"Authorization": f"Bearer {leaky_access_token}"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_json = response.json()
        assert response_json["error"] == "NotFoundError"
        assert response_json["error_msg"] == f'User "{user_does_not_exist}" not found.'
        assert response_json["msg"] is None
        assert response_json["data"] is None

    def test_get_todolists_todos_workspace_not_found_raises(self, client: TestClient, login_user: Tuple[TestUserInfo, str]) -> None:
        """Test that if the workspace does not exist, an error will be raised."""

        user, access_token = login_user

        workspace_does_not_exist = "workspace_does_not_exist"

        response = client.get(
            "/api/workspace/todolists/todos/?username={}&workspace_default_name={}".format(user.username, workspace_does_not_exist),
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_json = response.json()
        assert response_json["error"] == "NotFoundError"
        assert response_json["error_msg"] == f'Workspace "{workspace_does_not_exist}" not found.'
        assert response_json["msg"] is None
        assert response_json["data"] is None
    
    def test_user_get_todolists_todos_not_joined_raises(self, client: TestClient, login_users: Tuple[Tuple[TestUserInfo, str], Tuple[TestUserInfo, str]], test_workspace_info: TestWorkspaceInfo) -> None:
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

        response = client.get(
            "/api/workspace/todolists/todos/?username={}&workspace_default_name={}".format(user2.username, test_workspace_info.workspace_default_name),
            headers={"Authorization": f"Bearer {access_token2}"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_json = response.json()
        assert response_json["error"] == "NotFoundError"
        assert response_json["error_msg"] == f'User "{user2.username}" has not joined workspace "{test_workspace_info.workspace_default_name}".'
        assert response_json["msg"] is None
        assert response_json["data"] is None