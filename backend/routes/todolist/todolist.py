from fastapi import APIRouter, status, Request
from fastapi.responses import JSONResponse

from util.exceptions.api_exceptions import InvalidTokenError, TokenExpiredError, UnauthorizedError
from data_models import DatabaseConnection
from data_models.models import Account, TodoList, WorkSpace, WorkSpaceAccountLink
from sqlalchemy.exc import NoResultFound # type: ignore
from .schema import CreateTodoListModel, DeleteTodoListModel, ChangeTodoListNameModel
from util.helper.string import StringHashFactory
from util.helper.auth import JWTHandler
from util.exceptions import (NotFoundError, InternalServerError)
from typing import Final

router = APIRouter()

jwt_handler = JWTHandler()

hasher: Final = StringHashFactory().get_hasher("blake2b")

@router.post("/")
def create_todo_list(request: Request, create_model: CreateTodoListModel) -> JSONResponse:
    """Create a todo list."""
    
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

            new_todo_list = TodoList(
                workspace_id=workspace.workspace_id,
                todolist_name=create_model.todolist_name,
            )
            session.add(new_todo_list)
            session.commit()
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "error": None,
                "error_msg": None,
                "data": new_todo_list.todolist_id,
                "msg": f'Todolist "{create_model.todolist_name}" in workspace "{create_model.workspace_default_name}" created successfully.',
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
        else:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": NotFoundError.__name__,
                    "error_msg": f'User "{create_model.username}" not found.',
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
def change_todo_list_name(request: Request, change_name_model: ChangeTodoListNameModel) -> JSONResponse:
    """Change the name of a todo list."""
    
    try:
        authorization: str = request.headers.get("Authorization")

        if authorization is None:
            raise UnauthorizedError("Unauthorized action.")

        token = authorization.replace("Bearer ", "")
        payload = jwt_handler.get_payload(token)
        
        if "username" not in payload:
            raise InvalidTokenError("Invalid token.")
        
        if change_name_model.get_auth_user() != payload["username"]:
            raise UnauthorizedError("Unauthorized action.")

        with DatabaseConnection() as session:
            try:
                user: Account = session.query(Account).filter(Account.username == change_name_model.username).one()
            except NoResultFound as e:
                raise NotFoundError(f'User "{change_name_model.username}" not found.')
            
            try:
                workspace: WorkSpace = session.query(WorkSpace).filter(WorkSpace.workspace_default_name == change_name_model.workspace_default_name).one()
            except NoResultFound as e:
                raise NotFoundError(f'Workspace "{change_name_model.workspace_default_name}" not found.')
            
            try:
                session.query(WorkSpaceAccountLink).filter(WorkSpaceAccountLink.user_id == user.user_id, WorkSpaceAccountLink.workspace_id == workspace.workspace_id).one()
            except NoResultFound as e:
                raise NotFoundError(f'User "{change_name_model.username}" has not joined workspace "{change_name_model.workspace_default_name}".')

            try:
                todo_list: TodoList = session.query(TodoList).filter(TodoList.todolist_id == change_name_model.todolist_id).one()
            except NoResultFound as e:
                raise NotFoundError(f'Todo list of id "{change_name_model.todolist_id}" not found.')
            
            todo_list_orig_name = todo_list.todolist_name
            todo_list.todolist_name = change_name_model.new_todolist_name
            session.commit()
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "error": None,
                "error_msg": None,
                "data": None,
                "msg": f'User "{user.username}" has changed the name of todolist from "{todo_list_orig_name}" to "{change_name_model.new_todolist_name}" in workspace "{change_name_model.workspace_default_name}" successfully.'
            },
        )
    except NotFoundError as e:
        if "Workspace" in str(e):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": NotFoundError.__name__,
                    "error_msg": f'Workspace "{change_name_model.workspace_default_name}" not found.',
                    "data": None,
                    "msg": None,
                }
            )
        elif "User" in str(e) and "has not joined" in str(e):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": NotFoundError.__name__,
                    "error_msg": f'User "{change_name_model.username}" has not joined workspace "{change_name_model.workspace_default_name}".',
                    "data": None,
                    "msg": None,
                }
            )
        elif "Todo list" in str(e):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": NotFoundError.__name__,
                    "error_msg": f'Todo list of id "{change_name_model.todolist_id}" not found.',
                    "data": None,
                    "msg": None,
                }
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": NotFoundError.__name__,
                    "error_msg": f'User "{change_name_model.username}" not found.',
                    "data": None,
                    "msg": None,
                }
            )
    except UnauthorizedError as e:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": UnauthorizedError.__name__,
                "error_msg": "Unauthorized action.",
                "data": None,
                "msg": None,
            }
        )
    except TokenExpiredError as e:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": TokenExpiredError.__name__,
                "error_msg": "Token has expired.",
                "data": None,
                "msg": None,
            }
        )
    except InvalidTokenError as e:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": InvalidTokenError.__name__,
                "error_msg": "Invalid token.",
                "data": None,
                "msg": None,
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": InternalServerError.__name__,
                "error_msg": str(e),
                "data": None,
                "msg": None,
            }
        )

@router.delete("/")
def delete_todo_list(request: Request, delete_model: DeleteTodoListModel) -> JSONResponse:
    """Delete a todo list."""
    
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
                todo_list: TodoList = session.query(TodoList).filter(TodoList.todolist_id == delete_model.todolist_id).one()
            except NoResultFound as e:
                raise NotFoundError(f'Todo list of id "{delete_model.todolist_id}" not found.')
            
            session.delete(todo_list)
            session.commit()
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "error": None,
                "error_msg": None,
                "data": None,
                "msg": f'User "{user.username}" has deleted todolist "{todo_list.todolist_name}" in workspace "{delete_model.workspace_default_name}" successfully.',
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
                }
            )
        elif "User" in str(e) and "has not joined" in str(e):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": NotFoundError.__name__,
                    "error_msg": f'User "{delete_model.username}" has not joined workspace "{delete_model.workspace_default_name}".',
                    "data": None,
                    "msg": None,
                }
            )
        elif "Todo list" in str(e):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": NotFoundError.__name__,
                    "error_msg": f'Todo list of id "{delete_model.todolist_id}" not found.',
                    "data": None,
                    "msg": None,
                }
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": NotFoundError.__name__,
                    "error_msg": f'User "{delete_model.username}" not found.',
                    "data": None,
                    "msg": None,
                }
            )
    except UnauthorizedError as e:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": UnauthorizedError.__name__,
                "error_msg": "Unauthorized action.",
                "data": None,
                "msg": None,
            }
        )
    except TokenExpiredError as e:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": TokenExpiredError.__name__,
                "error_msg": "Token has expired.",
                "data": None,
                "msg": None,
            }
        )
    except InvalidTokenError as e:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": InvalidTokenError.__name__,
                "error_msg": "Invalid token.",
                "data": None,
                "msg": None,
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": InternalServerError.__name__,
                "error_msg": str(e),
                "data": None,
                "msg": None,
            }
        )