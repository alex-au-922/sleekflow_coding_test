from fastapi import APIRouter, Request, Query as FastAPIQuery, status as FastAPIHTTPStatus
from fastapi.responses import JSONResponse

from data_models import DatabaseConnection
from data_models.models import Account, TodoList, WorkSpace, WorkSpaceAccountLink, Todo
from data_models.filter_handler import FilterHandlerFactory
from .schema import CreateTodoListModel, ChangeTodoListNameModel
from util.helper.string import StringHashFactory
from util.helper.auth import auth_check
from util.exceptions import NotFoundError
from typing import Final, List, Literal, Optional
from data_models.query_wrapper import QueryWrapper
from sqlalchemy.orm import Query # type: ignore
from sqlalchemy import asc, desc # type: ignore

router = APIRouter()

hasher: Final = StringHashFactory().get_hasher("blake2b")

todo_filter_handler: Final = FilterHandlerFactory().get_handler("Todo")

@router.get("/todos/")
def get_todos(
    request: Request, 
    username: str,
    workspace_default_name: str,
    todolist_id: int,
    name: Optional[List[str]] = FastAPIQuery(default=[], regex=r"^\[(eq|gt|lt|ge|le|ne)\].*$"),
    description: Optional[List[str]] = FastAPIQuery(default=[], regex=r"^\[(eq|gt|lt|ge|le|ne)\].*$"),
    due_date: Optional[List[str]] = FastAPIQuery(default=[], regex=r"^\[(eq|gt|lt|ge|le|ne)\].*$"),
    priority: Optional[List[str]] = FastAPIQuery(default=[], regex=r"^\[(eq|gt|lt|ge|le|ne)\].*$"),
    status: Optional[List[str]] = FastAPIQuery(default=[], regex=r"^\[(eq|gt|lt|ge|le|ne)\].*$"),
    sort_by: Optional[Literal["name", "description", "due_date", "status", "priority"]] = None,
    order_by: Optional[Literal["asc", "desc"]] = "asc"
) -> JSONResponse:
    """Get all todos and filter or sort the data on request"""

    try:
        auth_check(request.headers.get("Authorization"), "username", username)
        

        with DatabaseConnection() as session:
            query_wrapper = QueryWrapper(session)
            user = query_wrapper.check_user_exists_and_get(username)
            query_wrapper.check_workspace_exists_and_get(workspace_default_name)
            todolist = query_wrapper.check_todolist_exists_and_get(todolist_id)
            query_wrapper.check_user_in_workspace_and_get(username, workspace_default_name)
            
            todo_query: Query = (
                session
                    .query(Todo)
                    .join(TodoList, TodoList.todolist_id == Todo.todolist_id)
                    .join(WorkSpace, WorkSpace.workspace_id == TodoList.workspace_id)
                    .join(WorkSpaceAccountLink, WorkSpaceAccountLink.workspace_id == WorkSpace.workspace_id)
                    .join(Account, WorkSpaceAccountLink.user_id == user.user_id)
                    .filter(WorkSpace.workspace_default_name == workspace_default_name)
                    .filter(Account.username == username)
                    .filter(TodoList.todolist_id == todolist_id)
            )

            if name is not None:
                for name_filter_specification in name:
                    todo_query = todo_filter_handler.register_filter(todo_query, "name", name_filter_specification).get_filter_query()

            if description is not None:
                for description_filter_specification in description:
                    todo_query = todo_filter_handler.register_filter(todo_query, "description", description_filter_specification).get_filter_query()
            
            if due_date is not None:
                for due_date_filter_specification in due_date:
                    todo_query = todo_filter_handler.register_filter(todo_query, "due_date", due_date_filter_specification).get_filter_query()
            
            if priority is not None:
                for priority_filter_specification in priority:
                    todo_query = todo_filter_handler.register_filter(todo_query, "priority", priority_filter_specification).get_filter_query()
            
            if status is not None:
                for status_filter_specification in status:
                    todo_query = todo_filter_handler.register_filter(todo_query, "status", status_filter_specification).get_filter_query()
            
            if sort_by is not None:
                if order_by == "asc":
                    todo_query = todo_query.order_by(
                        asc(getattr(Todo, sort_by))
                    )
                else:
                    todo_query = todo_query.order_by(
                        desc(getattr(Todo, sort_by))
                    )

            
            query_result: List[Todo] = todo_query.all()
            todos: List[dict] = [
                {
                    "todo_id": todo.todo_id,
                    "todo_name": todo.name,
                    "todo_description": todo.description,
                    "todo_due_date": str(todo.due_date),
                    "todo_priority": todo.priority,
                    "todo_status": todo.status,
                    "todo_last_modified": str(todo.last_modified)
                } for todo in query_result
            ]

        return JSONResponse(
            status_code=FastAPIHTTPStatus.HTTP_200_OK,
            content={
                "error": None,
                "error_msg": None,
                "data": todos,
                "msg": f'Get all todos in todolist "{todolist.todolist_name}" in workspace "{workspace_default_name}" successfully.',
            }
        )
    except NotFoundError as e:
        if "Workspace" in str(e):
            return JSONResponse(
                status_code=FastAPIHTTPStatus.HTTP_404_NOT_FOUND,
                content={
                    "error": NotFoundError.__name__,
                    "error_msg": f'Workspace "{workspace_default_name}" not found.',
                    "data": None,
                    "msg": None,
                },
            )
        elif "User" in str(e) and "has not joined" in str(e):
            return JSONResponse(
                status_code=FastAPIHTTPStatus.HTTP_404_NOT_FOUND,
                content={
                    "error": NotFoundError.__name__,
                    "error_msg": f'User "{username}" has not joined workspace "{workspace_default_name}".',
                    "data": None,
                    "msg": None,
                },
            )
        elif "User" in str(e):
            return JSONResponse(
                status_code=FastAPIHTTPStatus.HTTP_404_NOT_FOUND,
                content={
                    "error": NotFoundError.__name__,
                    "error_msg": f'User "{username}" not found.',
                    "data": None,
                    "msg": None,
                },
            )
        else:
            return JSONResponse(
                status_code=FastAPIHTTPStatus.HTTP_404_NOT_FOUND,
                content={
                    "error": NotFoundError.__name__,
                    "error_msg": f'Todo list of id "{todolist_id}" is not found in workspace "{workspace_default_name}".',
                    "data": None,
                    "msg": None,
                },
            )

@router.post("/")
def create_todo_list(request: Request, create_model: CreateTodoListModel) -> JSONResponse:
    """Create a todo list."""
    
    try:
        auth_check(request.headers.get("Authorization"), "username", create_model.get_auth_user())

        with DatabaseConnection() as session:
            query_wrapper = QueryWrapper(session)
            query_wrapper.check_user_exists_and_get(create_model.username)
            workspace = query_wrapper.check_workspace_exists_and_get(create_model.workspace_default_name)
            query_wrapper.check_user_in_workspace_and_get(create_model.username, create_model.workspace_default_name)
            
            new_todo_list = TodoList(
                workspace_id=workspace.workspace_id,
                todolist_name=create_model.todolist_name,
            )
            session.add(new_todo_list)
            session.commit()
        return JSONResponse(
            status_code=FastAPIHTTPStatus.HTTP_201_CREATED,
            content={
                "error": None,
                "error_msg": None,
                "data": new_todo_list.todolist_id,
                "msg": f'Todo list "{create_model.todolist_name}" in workspace "{create_model.workspace_default_name}" created successfully.',
            },
        )
    except NotFoundError as e:
        if "Workspace" in str(e):
            return JSONResponse(
                status_code=FastAPIHTTPStatus.HTTP_404_NOT_FOUND,
                content={
                    "error": NotFoundError.__name__,
                    "error_msg": f'Workspace "{create_model.workspace_default_name}" not found.',
                    "data": None,
                    "msg": None,
                },
            )
        elif "User" in str(e) and "has not joined" in str(e):
            return JSONResponse(
                status_code=FastAPIHTTPStatus.HTTP_404_NOT_FOUND,
                content={
                    "error": NotFoundError.__name__,
                    "error_msg": f'User "{create_model.username}" has not joined workspace "{create_model.workspace_default_name}".',
                    "data": None,
                    "msg": None,
                },
            )
        else:
            return JSONResponse(
                status_code=FastAPIHTTPStatus.HTTP_404_NOT_FOUND,
                content={
                    "error": NotFoundError.__name__,
                    "error_msg": f'User "{create_model.username}" not found.',
                    "data": None,
                    "msg": None,
                },
            )

@router.put("/")
def change_todo_list_name(request: Request, change_name_model: ChangeTodoListNameModel) -> JSONResponse:
    """Change the name of a todo list."""
    
    try:
        auth_check(request.headers.get("Authorization"), "username", change_name_model.get_auth_user())

        with DatabaseConnection() as session:

            query_wrapper = QueryWrapper(session)
            query_wrapper.check_user_exists_and_get(change_name_model.username)
            query_wrapper.check_workspace_exists_and_get(change_name_model.workspace_default_name)
            query_wrapper.check_user_in_workspace_and_get(change_name_model.username, change_name_model.workspace_default_name)
            todo_list = query_wrapper.check_todolist_exists_and_get(change_name_model.todolist_id)
            
            todo_list_orig_name = todo_list.todolist_name
            todo_list.todolist_name = change_name_model.new_todolist_name
            session.commit()
        return JSONResponse(
            status_code=FastAPIHTTPStatus.HTTP_202_ACCEPTED,
            content={
                "error": None,
                "error_msg": None,
                "data": None,
                "msg": f'User "{change_name_model.username}" has changed the name of todolist from "{todo_list_orig_name}" to "{change_name_model.new_todolist_name}" in workspace "{change_name_model.workspace_default_name}" successfully.'
            },
        )
    except NotFoundError as e:
        if "Workspace" in str(e):
            return JSONResponse(
                status_code=FastAPIHTTPStatus.HTTP_404_NOT_FOUND,
                content={
                    "error": NotFoundError.__name__,
                    "error_msg": f'Workspace "{change_name_model.workspace_default_name}" not found.',
                    "data": None,
                    "msg": None,
                }
            )
        elif "User" in str(e) and "has not joined" in str(e):
            return JSONResponse(
                status_code=FastAPIHTTPStatus.HTTP_404_NOT_FOUND,
                content={
                    "error": NotFoundError.__name__,
                    "error_msg": f'User "{change_name_model.username}" has not joined workspace "{change_name_model.workspace_default_name}".',
                    "data": None,
                    "msg": None,
                }
            )
        elif "Todo list" in str(e):
            return JSONResponse(
                status_code=FastAPIHTTPStatus.HTTP_404_NOT_FOUND,
                content={
                    "error": NotFoundError.__name__,
                    "error_msg": f'Todo list of id "{change_name_model.todolist_id}" not found in workspace "{change_name_model.workspace_default_name}".',
                    "data": None,
                    "msg": None,
                }
            )
        else:
            return JSONResponse(
                status_code=FastAPIHTTPStatus.HTTP_404_NOT_FOUND,
                content={
                    "error": NotFoundError.__name__,
                    "error_msg": f'User "{change_name_model.username}" not found.',
                    "data": None,
                    "msg": None,
                }
            )

@router.delete("/")
def delete_todo_list(request: Request, username: str, workspace_default_name: str, todolist_id: int) -> JSONResponse:
    """Delete a todo list."""
    
    try:
        auth_check(request.headers.get("Authorization"), "username", username)

        with DatabaseConnection() as session:
            query_wrapper = QueryWrapper(session)
            query_wrapper.check_user_exists_and_get(username)
            query_wrapper.check_workspace_exists_and_get(workspace_default_name)
            query_wrapper.check_user_in_workspace_and_get(username, workspace_default_name)
            todo_list = query_wrapper.check_todolist_exists_and_get(todolist_id)
            session.query(Todo).filter(Todo.todolist_id == todo_list.todolist_id).delete()
            session.delete(todo_list)
            session.commit()
        return JSONResponse(
            status_code=FastAPIHTTPStatus.HTTP_202_ACCEPTED,
            content={
                "error": None,
                "error_msg": None,
                "data": None,
                "msg": f'User "{username}" has deleted todolist "{todo_list.todolist_name}" in workspace "{workspace_default_name}" successfully.',
            },
        )
    except NotFoundError as e:
        if "Workspace" in str(e):
            return JSONResponse(
                status_code=FastAPIHTTPStatus.HTTP_404_NOT_FOUND,
                content={
                    "error": NotFoundError.__name__,
                    "error_msg": f'Workspace "{workspace_default_name}" not found.',
                    "data": None,
                    "msg": None,
                }
            )
        elif "User" in str(e) and "has not joined" in str(e):
            return JSONResponse(
                status_code=FastAPIHTTPStatus.HTTP_404_NOT_FOUND,
                content={
                    "error": NotFoundError.__name__,
                    "error_msg": f'User "{username}" has not joined workspace "{workspace_default_name}".',
                    "data": None,
                    "msg": None,
                }
            )
        elif "User" in str(e):
            return JSONResponse(
                status_code=FastAPIHTTPStatus.HTTP_404_NOT_FOUND,
                content={
                    "error": NotFoundError.__name__,
                    "error_msg": f'User "{username}" not found.',
                    "data": None,
                    "msg": None,
                }
            )
        elif "Todo list" in str(e):
            return JSONResponse(
                status_code=FastAPIHTTPStatus.HTTP_404_NOT_FOUND,
                content={
                    "error": NotFoundError.__name__,
                    "error_msg": f'Todo list of id "{todolist_id}" not found.',
                    "data": None,
                    "msg": None,
                }
            )
        else:
            return JSONResponse(
                status_code=FastAPIHTTPStatus.HTTP_404_NOT_FOUND,
                content={
                    "error": NotFoundError.__name__,
                    "error_msg": f'User "{username}" not found.',
                    "data": None,
                    "msg": None,
                }
            )