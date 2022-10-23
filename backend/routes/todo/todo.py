from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from util.exceptions import NotFoundError
from data_models import DatabaseConnection
from data_models.models import Todo
from .schema import CreateTodoModel, ChangeTodoModel
from util.helper.string import StringHashFactory
from util.helper.auth import auth_check
from typing import Final
from data_models.query_wrapper import QueryWrapper

router = APIRouter()
hasher: Final = StringHashFactory().get_hasher("blake2b")

@router.post("/")
def create_todo(request: Request, create_model: CreateTodoModel) -> JSONResponse:
    """Create a todo."""
    
    try:
        auth_check(request.headers.get("Authorization"), "username", create_model.get_auth_user())

        with DatabaseConnection() as session:

            query_wrapper = QueryWrapper(session)
            query_wrapper.check_user_exists_and_get(create_model.username)
            workspace = query_wrapper.check_workspace_exists_and_get(create_model.workspace_default_name)
            query_wrapper.check_user_in_workspace_and_get(create_model.username, create_model.workspace_default_name)
            todolist = query_wrapper.check_todolist_exists_and_get(create_model.todolist_id)

            new_todo = Todo(
                todolist_id = todolist.todolist_id,
                workspace_id = workspace.workspace_id,
                name = create_model.todo_name,
                description = create_model.todo_description,
                due_date = create_model.todo_due_date,
                status = create_model.todo_status,
                priority = create_model.todo_priority,
                last_modified = create_model.get_last_modified()
            )
            session.add(new_todo)
            session.commit()
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "error": None,
                "error_msg": None,
                "data": new_todo.todo_id,
                "msg":  f'Todo "{create_model.todo_name}" in todo list "{todolist.todolist_name}" in workspace "{workspace.workspace_default_name}" created successfully.',
            },
        )
    except NotFoundError as e:
        if "Workspace" in str(e):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": NotFoundError.__name__,
                    "error_msg": f'Workspace "{create_model.workspace_default_name}" not found.',
                    "data": None,
                    "msg": None,
                },
            )
        elif "User" in str(e) and "has not joined" in str(e):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": NotFoundError.__name__,
                    "error_msg": f'User "{create_model.username}" has not joined workspace "{create_model.workspace_default_name}".',
                    "data": None,
                    "msg": None,
                },
            )
        elif "User" in str(e):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": NotFoundError.__name__,
                    "error_msg": f'User "{create_model.username}" not found.',
                    "data": None,
                    "msg": None,
                },
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": NotFoundError.__name__,
                    "error_msg": f'Todo list of id "{create_model.todolist_id}" is not found in workspace "{create_model.workspace_default_name}".',
                    "data": None,
                    "msg": None,
                },
            )

@router.put("/")
def change_todo(request: Request, change_model: ChangeTodoModel) -> JSONResponse:
    """Change a todo."""
    
    try:
        auth_check(request.headers.get("Authorization"), "username", change_model.get_auth_user())

        with DatabaseConnection() as session:

            query_wrapper = QueryWrapper(session)

            query_wrapper.check_user_exists_and_get(change_model.username)
            query_wrapper.check_workspace_exists_and_get(change_model.workspace_default_name)
            query_wrapper.check_user_in_workspace_and_get(change_model.username, change_model.workspace_default_name)
            todolist = query_wrapper.check_todolist_exists_and_get(change_model.todolist_id)
            todo = query_wrapper.check_todo_exists_and_get(change_model.todo_id)
            
            todo_orig_name = todo.name

            changed: bool = False
            if change_model.todo_name:
                changed = True
                todo.name = change_model.todo_name
            if change_model.todo_description:
                changed = True
                todo.description = change_model.todo_description
            if change_model.todo_due_date:
                changed = True
                todo.due_date = change_model.todo_due_date
            if change_model.todo_priority:
                changed = True
                todo.priority = change_model.todo_priority
            if change_model.todo_status:
                changed = True
                todo.status = change_model.todo_status
            if changed:
                todo.last_modified = change_model.get_last_modified()
  
            session.commit()
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "error": None,
                "error_msg": None,
                "data": None,
                "msg":  f'Content of todo "{todo_orig_name}" has been modified in todo list "{todolist.todolist_name}" in workspace "{change_model.workspace_default_name}" successfully.'
            },
        )
    except NotFoundError as e:
        if "Workspace" in str(e):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": NotFoundError.__name__,
                    "error_msg": f'Workspace "{change_model.workspace_default_name}" not found.',
                    "data": None,
                    "msg": None,
                },
            )
        elif "User" in str(e) and "has not joined" in str(e):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": NotFoundError.__name__,
                    "error_msg": f'User "{change_model.username}" has not joined workspace "{change_model.workspace_default_name}".',
                    "data": None,
                    "msg": None,
                },
            )
        elif "User" in str(e):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": NotFoundError.__name__,
                    "error_msg": f'User "{change_model.username}" not found.',
                    "data": None,
                    "msg": None,
                },
            )
        elif "Todo list" in str(e):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": NotFoundError.__name__,
                    "error_msg": f'Todo list of id "{change_model.todolist_id}" is not found in workspace "{change_model.workspace_default_name}".',
                    "data": None,
                    "msg": None,
                },
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": NotFoundError.__name__,
                    "error_msg": f'Todo of id "{change_model.todo_id}" is not found in todo list of id "{change_model.todolist_id}" in workspace "{change_model.workspace_default_name}".',
                    "data": None,
                    "msg": None,
                },
            )

@router.delete("/")
def delete_todo(request: Request, username: str, workspace_default_name: str, todolist_id: int, todo_id: int) -> JSONResponse:
    """Delete a todo."""
    
    try:
        auth_check(request.headers.get("Authorization"), "username", username)


        with DatabaseConnection() as session:
            query_wrapper = QueryWrapper(session)

            query_wrapper.check_user_exists_and_get(username)
            query_wrapper.check_workspace_exists_and_get(workspace_default_name)
            query_wrapper.check_user_in_workspace_and_get(username, workspace_default_name)
            todolist = query_wrapper.check_todolist_exists_and_get(todolist_id)
            todo = query_wrapper.check_todo_exists_and_get(todo_id)
            
            todo_orig_name = todo.name

            session.delete(todo)
            
            session.commit()
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "error": None,
                "error_msg": None,
                "data": None,
                "msg":  f'Todo "{todo_orig_name}" has been deleted in todo list "{todolist.todolist_name}" in workspace "{workspace_default_name}" successfully.'
            },
        )
    except NotFoundError as e:
        if "Workspace" in str(e):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": NotFoundError.__name__,
                    "error_msg": f'Workspace "{workspace_default_name}" not found.',
                    "data": None,
                    "msg": None,
                },
            )
        elif "User" in str(e) and "has not joined" in str(e):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": NotFoundError.__name__,
                    "error_msg": f'User "{username}" has not joined workspace "{workspace_default_name}".',
                    "data": None,
                    "msg": None,
                },
            )
        elif "User" in str(e):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": NotFoundError.__name__,
                    "error_msg": f'User "{username}" not found.',
                    "data": None,
                    "msg": None,
                },
            )
        elif "Todo list" in str(e):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": NotFoundError.__name__,
                    "error_msg": f'Todo list of id "{todolist_id}" is not found in workspace "{workspace_default_name}".',
                    "data": None,
                    "msg": None,
                },
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": NotFoundError.__name__,
                    "error_msg": f'Todo of id "{todo_id}" is not found in todo list of id "{todolist_id}" in workspace "{workspace_default_name}".',
                    "data": None,
                    "msg": None,
                },
            )