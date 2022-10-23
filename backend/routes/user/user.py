from fastapi import APIRouter, status, Request
from fastapi.responses import JSONResponse
from .schema import UpdatePasswordModel, CreateUserModel
from data_models import DatabaseConnection
from data_models.models import Account
from sqlalchemy.exc import IntegrityError, NoResultFound # type: ignore
from util.helper.string import StringHashFactory
from sqlalchemy.exc import IntegrityError, NoResultFound # type: ignore
from util.exceptions import (DuplicateError,InvalidCredentialsError, NotFoundError, InternalServerError, InvalidTokenError, TokenExpiredError, UnauthorizedError)
from sqlalchemy.orm import Query # type: ignore
from util.helper.auth import JWTHandler
from data_models.models import Account, WorkSpace, WorkSpaceAccountLink
from typing import Final, List, Optional, Tuple

router = APIRouter()

jwt_handler = JWTHandler()

hasher: Final = StringHashFactory().get_hasher("blake2b")

@router.post("/")
def create_user(user: CreateUserModel) -> JSONResponse:
    """Create a user."""

    salt = hasher.create_salt()
    password_hash = hasher.hash(string=user.password, salt=salt)
    
    try:
        with DatabaseConnection() as session:
            new_user = Account(
                username=user.username,
                email=user.email,
                password_hash=password_hash,
                password_salt=salt,
            )
            session.add(new_user)
            session.commit()
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "error": None,
                "error_msg": None,
                "data": None,
                "msg": f'User "{user.username}" created successfully.',
            },
        )
    except IntegrityError as e:
        if 'Key (username)' in str(e):
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={
                    "error": DuplicateError.__name__,
                    "error_msg": f'Username "{user.username}" already exists.',
                    "data": None,
                    "msg": None,
                },
            )
        elif 'Key (email)' in str(e):
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={
                    "error": DuplicateError.__name__,
                    "error_msg": f'Email "{user.email}" already exists.',
                    "data": None,
                    "msg": None,
                },
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "InternalError",
                    "error_msg": str(e),
                    "data": None,
                    "msg": None,
                },
            )
    except Exception as e:
        print(e)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": InternalServerError.__name__,
                "error_msg": str(e),
                "data": None,
                "msg": None,
            },
        )

@router.put("/password/")
def update_user_password(user: UpdatePasswordModel) -> JSONResponse:
    """User update their password"""
    
    try:
        with DatabaseConnection() as session:
            query_user: Account = session.query(Account).filter(Account.username == user.username).one()
            old_password_salt = query_user.password_salt
            if not hasher.verify(string = user.old_password,salt = old_password_salt, hash = query_user.password_hash):
                raise InvalidCredentialsError("Invalid credentials.")
            
            new_password_salt = hasher.create_salt()
            new_password_hash = hasher.hash(string=user.new_password, salt=new_password_salt)
            query_user.password_hash = new_password_hash
            query_user.password_salt = new_password_salt
            session.commit()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "error": None,
                "error_msg": None,
                "data": None,
                "msg": "Password updated successfully.",
            },
        )
    except (NoResultFound, InvalidCredentialsError) as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": InvalidCredentialsError.__name__,
                "error_msg": 'Invalid credentials.',
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

@router.get("/workspace/")
def get_all_workspaces(request: Request, username: str) -> JSONResponse:
    """For the user with username, get all workspaces he or she has."""
    
    try:
        authorization: str = request.headers.get("Authorization")

        if authorization is None:
            raise UnauthorizedError("Unauthorized action.")

        token = authorization.replace("Bearer ", "")
        payload = jwt_handler.get_payload(token)
        
        if "username" not in payload:
            raise InvalidTokenError("Invalid token.")
        
        if username != payload["username"]:
            raise UnauthorizedError("Unauthorized action.")

        with DatabaseConnection() as session:    
            user: Account = session.query(Account).filter(Account.username == username).one()        
            query: Query = (
                session
                    .query(WorkSpace)
                    .join(WorkSpaceAccountLink, WorkSpaceAccountLink.workspace_id == WorkSpace.workspace_id)
                    .join(Account, WorkSpaceAccountLink.user_id == user.user_id)
                    .filter(Account.username == username)
                    .add_columns(WorkSpaceAccountLink.locale_alias)
            )
            query_result: List[Tuple[WorkSpace, Optional[str]]] = query.all()
            workspaces_details = [
                {
                    "workspace_default_name": workspace.workspace_default_name,
                    "workspace_alias": workspace_alias,
                }
                for workspace, workspace_alias in query_result
            ]
            session.commit()
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "error": None,
                "error_msg": None,
                "data": workspaces_details,
                "msg": f'Get all workspaces joined by "{username}" successfully.',
            },
        )
    except NoResultFound as e:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": NotFoundError.__name__,
                "error_msg": f'User "{username}" not found.',
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