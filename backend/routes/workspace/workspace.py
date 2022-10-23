from fastapi import APIRouter, status, Request
from fastapi.responses import JSONResponse

from .schema import CreateWorkspaceModel, InviteWorkspaceModel, ChangeWorkspaceAliasModel
from data_models import DatabaseConnection
from data_models.models import Account, Todo, TodoList, WorkSpace, WorkSpaceAccountLink
from sqlalchemy.exc import IntegrityError # type: ignore
from util.helper.string import StringHashFactory
from util.helper.auth import auth_check
from util.exceptions import (DuplicateError, NotFoundError, UnauthorizedError)
from typing import Dict, Final, List, Tuple
from sqlalchemy.orm import Query # type: ignore
from data_models.query_wrapper import QueryWrapper

router = APIRouter()

hasher: Final = StringHashFactory().get_hasher("blake2b")

@router.get("/todolists/todos/")
def get_all_todolists_todos(request: Request, username: str, workspace_default_name: str) -> JSONResponse:
    """Get a list of all workspaces"""
    
    try:
        auth_check(request.headers.get("Authorization"), "username", username)
        
        with DatabaseConnection() as session:
            query_wrapper = QueryWrapper(session)
            user = query_wrapper.check_user_exists_and_get(username)
            query_wrapper.check_workspace_exists_and_get(workspace_default_name)
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
                    .add_columns(TodoList.todolist_id)
            )

            todolist_query: Query = (
                session
                    .query(TodoList)
                    .join(WorkSpace, WorkSpace.workspace_id == TodoList.workspace_id)
                    .join(WorkSpaceAccountLink, WorkSpaceAccountLink.workspace_id == WorkSpace.workspace_id)
                    .join(Account, WorkSpaceAccountLink.user_id == user.user_id)
                    .filter(WorkSpace.workspace_default_name == workspace_default_name)
                    .filter(Account.username == username)
            )

            todolist_query_result: List[TodoList] = todolist_query.all()
            todo_query_result: List[Tuple[Todo, str]] = todo_query.all()

            todo_query_result_map: Dict[str, List[Dict]] = {}
            for todo, todolist_id in todo_query_result:
                if todolist_id not in todo_query_result_map:
                    todo_query_result_map[todolist_id] = []
                todo_query_result_map[todolist_id].append({
                    "todo_id": todo.todo_id,
                    "todo_name": todo.name,
                    "todo_description": todo.description,
                    "todo_due_date": str(todo.due_date),
                    "todo_priority": todo.priority,
                    "todo_status": todo.status,
                    "todo_last_modified": str(todo.last_modified),
                })

            query_result = [
                {
                    "todolist_id": todolist.todolist_id,
                    "todolist_name": todolist.todolist_name,
                    "todos": todo_query_result_map.get(todolist.todolist_id, [])
                }
                for todolist in todolist_query_result
            ]

            session.commit()
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "error": None,
                "error_msg": None,
                "data": query_result,
                "msg": f'Get all todolists and corresponding todos in workspace "{workspace_default_name}" successfully.',
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
        else:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": NotFoundError.__name__,
                    "error_msg": f'User "{username}" not found.',
                    "data": None,
                    "msg": None,
                },
            )

@router.post("/")
def create_workspace(request: Request, create_model: CreateWorkspaceModel) -> JSONResponse:
    """Create a workspace."""
    
    try:
        auth_check(request.headers.get("Authorization"), "username", create_model.get_auth_user())


        with DatabaseConnection() as session:
            query_wrapper = QueryWrapper(session)
            user = query_wrapper.check_user_exists_and_get(create_model.get_auth_user())

            new_workspace: WorkSpace = WorkSpace(
                workspace_owner_id = user.user_id,
                workspace_default_name = create_model.workspace_default_name,
            )
            workspace_account_record = WorkSpaceAccountLink(
                user_id = user.user_id,
                workspace_id = new_workspace.workspace_id,
            )
            new_workspace.members.append(workspace_account_record)
            session.add(new_workspace)
            session.commit()
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "error": None,
                "error_msg": None,
                "data": None,
                "msg": f'Workspace "{new_workspace.workspace_default_name}" created successfully.',
            },
        )
    except NotFoundError as e:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": NotFoundError.__name__,
                "error_msg": f'User "{create_model.username}" not found.',
                "data": None,
                "msg": None,
            },
        )
    except IntegrityError as e:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": DuplicateError.__name__,
                "error_msg": f'Workspace "{new_workspace.workspace_default_name}" already exists.',
                "data": None,
                "msg": None,
            },
        )

@router.put("/invite/")
def invite_user_to_workspace(request: Request, invite_model: InviteWorkspaceModel) -> JSONResponse:
    """Invite user to a workspace"""
    try:
        auth_check(request.headers.get("Authorization"), "username", invite_model.get_auth_user())
    
        with DatabaseConnection() as session:
            query_wrapper = QueryWrapper(session)
            owner = query_wrapper.check_user_exists_and_get(invite_model.owner_username)
            workspace = query_wrapper.check_workspace_exists_and_get(invite_model.workspace_default_name)
            invitee = query_wrapper.check_user_exists_and_get(invite_model.invitee_username)

            if workspace.workspace_owner_id != owner.user_id:
                raise UnauthorizedError("Unauthorized action.")

            workspace_account_record = WorkSpaceAccountLink(
                user_id = invitee.user_id,
                workspace_id = workspace.workspace_id,
            )

            session.add(workspace_account_record)
            session.commit()

        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "error": None,
                "error_msg": None,
                "data": None,
                "msg": f'Invited user "{invite_model.invitee_username}" to workspace "{invite_model.workspace_default_name}" successfully.',
            },
        )
    except NotFoundError as e:
        if "Workspace" in str(e):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": NotFoundError.__name__,
                    "error_msg": f'Workspace "{invite_model.workspace_default_name}" not found.',
                    "data": None,
                    "msg": None,
                },
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": NotFoundError.__name__,
                    "error_msg": f'User "{invite_model.invitee_username}" not found.',
                    "data": None,
                    "msg": None,
                },
            )
    except IntegrityError as e:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": DuplicateError.__name__,
                "error_msg": f'User "{invite_model.invitee_username}" has already joined workspace "{invite_model.workspace_default_name}".',
                "data": None,
                "msg": None,
            },
        )

@router.delete("/")
def leave_workspace(request: Request, username: str, workspace_default_name: str) -> JSONResponse:
    """When a user wants to leave the workspace"""

    try:
        auth_check(request.headers.get("Authorization"), "username", username)

        with DatabaseConnection() as session:
            
            query_wrapper = QueryWrapper(session)
            user = query_wrapper.check_user_exists_and_get(username)
            workspace = query_wrapper.check_workspace_exists_and_get(workspace_default_name)
            workspace_account_record = query_wrapper.check_user_in_workspace_and_get(username, workspace_default_name)

            if workspace.workspace_owner_id == user.user_id:
                session.query(Todo).filter(Todo.workspace_id == workspace.workspace_id).delete()
                session.query(TodoList).filter(TodoList.workspace_id == workspace.workspace_id).delete()
                session.query(WorkSpaceAccountLink).filter(WorkSpaceAccountLink.workspace_id == workspace.workspace_id).delete()
                session.delete(workspace)
            else:
                session.delete(workspace_account_record)

            session.commit()

        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "error": None,
                "error_msg": None,
                "data": None,
                "msg": f'User "{username}" has left workspace "{workspace_default_name}" successfully.',
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
        else:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": NotFoundError.__name__,
                    "error_msg": f'User "{username}" not found.',
                    "data": None,
                    "msg": None,
                },
            )

@router.put("/alias/")
def change_workspace_alias(request: Request, change_alias_model: ChangeWorkspaceAliasModel) -> JSONResponse:
    try:
        auth_check(request.headers.get("Authorization"), "username", change_alias_model.get_auth_user())
        
        with DatabaseConnection() as session:
            query_wrapper = QueryWrapper(session)
            query_wrapper.check_user_exists_and_get(change_alias_model.username)
            query_wrapper.check_workspace_exists_and_get(change_alias_model.workspace_default_name)
            workspace_account_record = query_wrapper.check_user_in_workspace_and_get(change_alias_model.username, change_alias_model.workspace_default_name)
          
            workspace_account_record_orig_alias = workspace_account_record.locale_alias
            workspace_account_record.locale_alias = change_alias_model.new_workspace_alias
            session.commit()
        
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "error": None,
                "error_msg": None,
                "data": None,
                "msg": f'User "{change_alias_model.username}" has changed the workspace "{change_alias_model.workspace_default_name}" alias from "{workspace_account_record_orig_alias}" to "{change_alias_model.new_workspace_alias}" successfully.',
            },
        )
    except NotFoundError as e:
        if "Workspace" in str(e):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": NotFoundError.__name__,
                    "error_msg": f'Workspace "{change_alias_model.workspace_default_name}" not found.',
                    "data": None,
                    "msg": None,
                },
            )
        elif "User" in str(e) and "has not joined" in str(e):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": NotFoundError.__name__,
                    "error_msg": f'User "{change_alias_model.username}" not found in workspace "{change_alias_model.workspace_default_name}".',
                    "data": None,
                    "msg": None,
                },
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": NotFoundError.__name__,
                    "error_msg": f'User "{change_alias_model.username}" not found.',
                    "data": None,
                    "msg": None,
                },
            )
