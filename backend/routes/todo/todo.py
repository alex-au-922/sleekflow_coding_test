from fastapi import APIRouter, status, Request
from fastapi.responses import JSONResponse

from util.exceptions.api_exceptions import InvalidTokenError, TokenExpiredError, UnauthorizedError
from data_models import DatabaseConnection
from data_models.models import Account, TodoList, WorkSpace, WorkSpaceAccountLink, Todo
from sqlalchemy.exc import NoResultFound # type: ignore
from .schema import CreateTodoModel, ChangeTodoModel, DeleteTodoModel
from util.helper.string import StringHashFactory
from util.helper.auth import JWTHandler
from util.exceptions import (NotFoundError, InternalServerError)
from typing import Final

router = APIRouter()

jwt_handler = JWTHandler()

hasher: Final = StringHashFactory().get_hasher("blake2b")

@router.post("/")
def create_todo(request: Request, create_model: CreateTodoModel) -> JSONResponse:
    """Create a todo."""
    
    try:
        authorization: str = request.headers.get("Authorization")

        if authorization is None:
            raise UnauthorizedError("Unauthorized action.")

        token = authorization.replace("Bearer ", "")
        payload = jwt_handler.get_payload(token)
        
        if "username" not in payload:
            raise InvalidTokenError("Invalid token.")
        
        if create_model.get_auth_user() != payload["username"]:
            raise UnauthorizedError("Unauthorized action.")

        with DatabaseConnection() as session:
            try:
                user: Account = session.query(Account).filter(Account.username == create_model.get_auth_user()).one()
            except NoResultFound as e:
                raise NotFoundError(f'User "{create_model.username}" not found.')
            
            try:
                workspace: WorkSpace = session.query(WorkSpace).filter(WorkSpace.workspace_default_name == create_model.workspace_default_name).one()
            except NoResultFound as e:
                raise NotFoundError(f'Workspace "{create_model.workspace_default_name}" not found.')
            
            try:
                session.query(WorkSpaceAccountLink).filter(WorkSpaceAccountLink.user_id == user.user_id, WorkSpaceAccountLink.workspace_id == workspace.workspace_id).one()
            except NoResultFound as e:
                raise NotFoundError(f'User "{create_model.username}" has not joined workspace "{create_model.workspace_default_name}".')

            try:
                todolist: TodoList = session.query(TodoList).filter(TodoList.todolist_id == create_model.todolist_id).one()
            except NoResultFound as e:
                raise NotFoundError(f'TodoList of id "{create_model.todolist_id}" not found.')

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
                "msg":  f'Todo "{create_model.todo_name}" in todo list "{todolist.todolist_name}" workspace "{workspace.workspace_default_name}" created successfully.',
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
    except UnauthorizedError as e:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": UnauthorizedError.__name__,
                "error_msg": "Unauthorized action.",
                "data": None,
                "msg": None,
            },
        )
    except TokenExpiredError as e:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": TokenExpiredError.__name__,
                "error_msg": "Token has expired.",
                "data": None,
                "msg": None,
            },
        )
    except InvalidTokenError as e:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": InvalidTokenError.__name__,
                "error_msg": "Invalid token.",
                "data": None,
                "msg": None,
            },
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": InternalServerError.__name__,
                "error_msg": str(e),
                "data": None,
                "msg": None,
            },
        )

@router.put("/")
def change_todo(request: Request, change_model: ChangeTodoModel) -> JSONResponse:
    """Change a todo."""
    
    try:
        authorization: str = request.headers.get("Authorization")

        if authorization is None:
            raise UnauthorizedError("Unauthorized action.")

        token = authorization.replace("Bearer ", "")
        payload = jwt_handler.get_payload(token)
        
        if "username" not in payload:
            raise InvalidTokenError("Invalid token.")
        
        if change_model.get_auth_user() != payload["username"]:
            raise UnauthorizedError("Unauthorized action.")

        with DatabaseConnection() as session:
            try:
                user: Account = session.query(Account).filter(Account.username == change_model.get_auth_user()).one()
            except NoResultFound as e:
                raise NotFoundError(f'User "{change_model.username}" not found.')
            
            try:
                workspace: WorkSpace = session.query(WorkSpace).filter(WorkSpace.workspace_default_name == change_model.workspace_default_name).one()
            except NoResultFound as e:
                raise NotFoundError(f'Workspace "{change_model.workspace_default_name}" not found.')
            
            try:
                session.query(WorkSpaceAccountLink).filter(WorkSpaceAccountLink.user_id == user.user_id, WorkSpaceAccountLink.workspace_id == workspace.workspace_id).one()
            except NoResultFound as e:
                raise NotFoundError(f'User "{change_model.username}" has not joined workspace "{change_model.workspace_default_name}".')

            try:
                todolist: TodoList = session.query(TodoList).filter(TodoList.todolist_id == change_model.todolist_id).one()
            except NoResultFound as e:
                raise NotFoundError(f'TodoList of id "{change_model.todolist_id}" not found.')

            try:
                todo: Todo = session.query(Todo).filter(Todo.todo_id == change_model.todo_id).one()
            except NoResultFound as e:
                raise NotFoundError(f'Todo of id "{change_model.todo_id}" not found.')
            
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
                "msg":  f'Content of todo "{todo_orig_name}" has been modified in todo list "{todolist.todolist_name}" workspace "{change_model.workspace_default_name}" successfully.'
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
        elif "TodoList" in str(e):
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
    except UnauthorizedError as e:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": UnauthorizedError.__name__,
                "error_msg": "Unauthorized action.",
                "data": None,
                "msg": None,
            },
        )
    except TokenExpiredError as e:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": TokenExpiredError.__name__,
                "error_msg": "Token has expired.",
                "data": None,
                "msg": None,
            },
        )
    except InvalidTokenError as e:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": InvalidTokenError.__name__,
                "error_msg": "Invalid token.",
                "data": None,
                "msg": None,
            },
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": InternalServerError.__name__,
                "error_msg": str(e),
                "data": None,
                "msg": None,
            },
        )

@router.delete("/")
def delete_todo(request: Request, delete_model: DeleteTodoModel) -> JSONResponse:
    """Delete a todo."""
    
    try:
        authorization: str = request.headers.get("Authorization")

        if authorization is None:
            raise UnauthorizedError("Unauthorized action.")

        token = authorization.replace("Bearer ", "")
        payload = jwt_handler.get_payload(token)
        
        if "username" not in payload:
            raise InvalidTokenError("Invalid token.")
        
        if delete_model.get_auth_user() != payload["username"]:
            raise UnauthorizedError("Unauthorized action.")

        with DatabaseConnection() as session:
            try:
                user: Account = session.query(Account).filter(Account.username == delete_model.get_auth_user()).one()
            except NoResultFound as e:
                raise NotFoundError(f'User "{delete_model.username}" not found.')
            
            try:
                workspace: WorkSpace = session.query(WorkSpace).filter(WorkSpace.workspace_default_name == delete_model.workspace_default_name).one()
            except NoResultFound as e:
                raise NotFoundError(f'Workspace "{delete_model.workspace_default_name}" not found.')
            
            try:
                session.query(WorkSpaceAccountLink).filter(WorkSpaceAccountLink.user_id == user.user_id, WorkSpaceAccountLink.workspace_id == workspace.workspace_id).one()
            except NoResultFound as e:
                raise NotFoundError(f'User "{delete_model.username}" has not joined workspace "{delete_model.workspace_default_name}".')

            try:
                todolist: TodoList = session.query(TodoList).filter(TodoList.todolist_id == delete_model.todolist_id).one()
            except NoResultFound as e:
                raise NotFoundError(f'TodoList of id "{delete_model.todolist_id}" not found.')

            try:
                todo: Todo = session.query(Todo).filter(Todo.todo_id == delete_model.todo_id).one()
            except NoResultFound as e:
                raise NotFoundError(f'Todo of id "{delete_model.todo_id}" not found.')
            
            todo_orig_name = todo.name

            session.delete(todo)
            
            session.commit()
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "error": None,
                "error_msg": None,
                "data": None,
                "msg":  f'Todo "{todo_orig_name}" has been deleted in todo list "{todolist.todolist_name}" workspace "{delete_model.workspace_default_name}" successfully.'
            },
        )
    except NotFoundError as e:
        if "Workspace" in str(e):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": NotFoundError.__name__,
                    "error_msg": f'Workspace "{delete_model.workspace_default_name}" not found.',
                    "data": None,
                    "msg": None,
                },
            )
        elif "User" in str(e) and "has not joined" in str(e):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": NotFoundError.__name__,
                    "error_msg": f'User "{delete_model.username}" has not joined workspace "{delete_model.workspace_default_name}".',
                    "data": None,
                    "msg": None,
                },
            )
        elif "User" in str(e):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": NotFoundError.__name__,
                    "error_msg": f'User "{delete_model.username}" not found.',
                    "data": None,
                    "msg": None,
                },
            )
        elif "TodoList" in str(e):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": NotFoundError.__name__,
                    "error_msg": f'Todo list of id "{delete_model.todolist_id}" is not found in workspace "{delete_model.workspace_default_name}".',
                    "data": None,
                    "msg": None,
                },
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": NotFoundError.__name__,
                    "error_msg": f'Todo of id "{delete_model.todo_id}" is not found in todo list of id "{delete_model.todolist_id}" in workspace "{delete_model.workspace_default_name}".',
                    "data": None,
                    "msg": None,
                },
            )
    except UnauthorizedError as e:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": UnauthorizedError.__name__,
                "error_msg": "Unauthorized action.",
                "data": None,
                "msg": None,
            },
        )
    except TokenExpiredError as e:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": TokenExpiredError.__name__,
                "error_msg": "Token has expired.",
                "data": None,
                "msg": None,
            },
        )
    except InvalidTokenError as e:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": InvalidTokenError.__name__,
                "error_msg": "Invalid token.",
                "data": None,
                "msg": None,
            },
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": InternalServerError.__name__,
                "error_msg": str(e),
                "data": None,
                "msg": None,
            },
        )
