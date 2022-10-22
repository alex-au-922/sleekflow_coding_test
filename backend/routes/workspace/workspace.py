from fastapi import APIRouter, status, Request
from fastapi.responses import JSONResponse

from util.exceptions.api_exceptions import InvalidTokenError, TokenExpiredError, UnauthorizedError
from .schema import CreateWorkspaceModel, InviteWorkspaceModel, LeaveWorkspaceModel
from data_models import DatabaseConnection
from data_models.models import Account, WorkSpace, WorkSpaceAccountLink
from sqlalchemy.exc import IntegrityError, NoResultFound # type: ignore
from util.helper.string import StringHashFactory
from util.helper.auth import JWTHandler
from util.exceptions import (DuplicateError, NotFoundError, InternalServerError)
from typing import Final

router = APIRouter()

jwt_handler = JWTHandler()

hasher: Final = StringHashFactory().get_hasher("blake2b")

@router.post("/")
def create_workspace(request: Request, workspace: CreateWorkspaceModel) -> JSONResponse:
    """Create a workspace."""
    
    try:
        authorization: str = request.headers.get("Authorization")

        if authorization is None:
            raise UnauthorizedError("Unauthorized action.")

        token = authorization.replace("Bearer ", "")
        payload = jwt_handler.get_payload(token)
        
        if "username" not in payload:
            raise InvalidTokenError("Invalid token.")
        
        if workspace.get_auth_user() != payload["username"]:
            raise UnauthorizedError("Unauthorized action.")

        with DatabaseConnection() as session:

            user: Account = session.query(Account).filter(Account.username == workspace.username).one()

            new_workspace: WorkSpace = WorkSpace(
                workspace_owner_id = user.user_id,
                workspace_default_name = workspace.workspace_default_name,
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
                "data": new_workspace.workspace_id,
                "msg": f'Workspace "{new_workspace.workspace_default_name}" created successfully.',
            },
        )
    except NoResultFound as e:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": NotFoundError.__name__,
                "error_msg": f'User "{workspace.username}" not found.',
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

@router.put("/invite/")
def invite_user_to_workspace(request: Request, invite_model: InviteWorkspaceModel) -> JSONResponse:
    """Invite user to a workspace"""

    try:
        authorization: str = request.headers.get("Authorization")

        if authorization is None:
            raise UnauthorizedError("Unauthorized action.")

        token = authorization.replace("Bearer ", "")
        payload = jwt_handler.get_payload(token)
        
        if "username" not in payload:
            raise InvalidTokenError("Invalid token.")
        
        if invite_model.get_auth_user() != payload["username"]:
            raise UnauthorizedError("Unauthorized action.")
    
        with DatabaseConnection() as session:
            
            try:
                workspace: WorkSpace = session.query(WorkSpace).filter(WorkSpace.workspace_default_name == invite_model.workspace_default_name).one()
            except NoResultFound as e:
                raise NotFoundError(f'Workspace "{invite_model.workspace_default_name}" not found.')

            owner: Account = session.query(Account).filter(Account.username == invite_model.owner_username).one()

            if workspace.workspace_owner_id != owner.user_id:
                raise UnauthorizedError("Unauthorized action.")
            
            try:
                invitee: Account = session.query(Account).filter(Account.username == invite_model.invitee_username).one()
            except NoResultFound as e:
                raise NotFoundError(f'User "{invite_model.invitee_username}" not found.')

            workspace_account_record = WorkSpaceAccountLink(
                user_id = invitee.user_id,
                workspace_id = workspace.workspace_id,
            )
            workspace.members.append(workspace_account_record)
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

@router.delete("/leave/")
def leave_workspace(request: Request, leave_model: LeaveWorkspaceModel) -> JSONResponse:
    """When a user wants to leave the workspace"""

    try:
        authorization: str = request.headers.get("Authorization")

        if authorization is None:
            raise UnauthorizedError("Unauthorized action.")

        token = authorization.replace("Bearer ", "")
        payload = jwt_handler.get_payload(token)
        
        if "username" not in payload:
            raise InvalidTokenError("Invalid token.")
        
        if leave_model.get_auth_user() != payload["username"]:
            raise UnauthorizedError("Unauthorized action.")

        with DatabaseConnection() as session:
            
            try:
                workspace: WorkSpace = session.query(WorkSpace).filter(WorkSpace.workspace_default_name == leave_model.workspace_default_name).one()
            except NoResultFound as e:
                raise NotFoundError(f'Workspace "{invite_model.workspace_default_name}" not found.')

            owner: Account = session.query(Account).filter(Account.username == invite_model.owner_username).one()

            if workspace.workspace_owner_id != owner.user_id:
                raise UnauthorizedError("Unauthorized action.")
            
            try:
                invitee: Account = session.query(Account).filter(Account.username == invite_model.invitee_username).one()
            except NoResultFound as e:
                raise NotFoundError(f'User "{invite_model.invitee_username}" not found.')

            workspace_account_record = WorkSpaceAccountLink(
                user_id = invitee.user_id,
                workspace_id = workspace.workspace_id,
            )
            workspace.members.append(workspace_account_record)
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