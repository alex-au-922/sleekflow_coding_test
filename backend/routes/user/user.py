from fastapi import APIRouter, status, Request
from fastapi.responses import JSONResponse

from .schema import UpdatePasswordModel, CreateUserModel
from data_models import DatabaseConnection
from data_models.models import Account
from sqlalchemy.exc import IntegrityError # type: ignore
from util.helper.string import StringHashFactory
from util.exceptions import DuplicateError,InvalidCredentialsError, NotFoundError
from sqlalchemy.orm import Query # type: ignore
from util.helper.auth import auth_check
from data_models.models import Account, WorkSpace, WorkSpaceAccountLink
from typing import Final, List, Optional, Tuple
from data_models.query_wrapper import QueryWrapper

router = APIRouter()

hasher: Final = StringHashFactory().get_hasher("blake2b")

@router.post("/")
def create_user(create_model: CreateUserModel) -> JSONResponse:
    """Create a user."""

    salt = hasher.create_salt()
    password_hash = hasher.hash(string=create_model.password, salt=salt)
    
    try:
        with DatabaseConnection() as session:
            new_user = Account(
                username=create_model.username,
                email=create_model.email,
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
                "msg": f'User "{create_model.username}" created successfully.',
            },
        )
    except IntegrityError as e:
        if 'Key (username)' in str(e):
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={
                    "error": DuplicateError.__name__,
                    "error_msg": f'Username "{create_model.username}" already exists.',
                    "data": None,
                    "msg": None,
                },
            )
        elif 'Key (email)' in str(e):
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={
                    "error": DuplicateError.__name__,
                    "error_msg": f'Email "{create_model.email}" already exists.',
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

@router.put("/password/")
def update_user_password(update_model: UpdatePasswordModel) -> JSONResponse:
    """User update their password"""
    
    try:
        with DatabaseConnection() as session:
            query_wrapper = QueryWrapper(session)
            user = query_wrapper.check_user_exists_and_get(username=update_model.username)
            
            old_password_salt = user.password_salt
            if not hasher.verify(string = update_model.old_password,salt = old_password_salt, hash = user.password_hash):
                raise InvalidCredentialsError("Invalid credentials.")
            
            new_password_salt = hasher.create_salt()
            new_password_hash = hasher.hash(string=update_model.new_password, salt=new_password_salt)
            user.password_hash = new_password_hash
            user.password_salt = new_password_salt
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
    except (NotFoundError, InvalidCredentialsError) as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": InvalidCredentialsError.__name__,
                "error_msg": 'Invalid credentials.',
                "data": None,
                "msg": None,
            },
        )

@router.get("/workspace/")
def get_all_workspaces(request: Request, username: str) -> JSONResponse:
    """For the user with username, get all workspaces he or she has."""
    
    try:
        auth_check(request.headers.get("Authorization"), "username", username)

        with DatabaseConnection() as session:   
            query_wrapper = QueryWrapper(session)
            user = query_wrapper.check_user_exists_and_get(username=username)
          
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
    except NotFoundError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": NotFoundError.__name__,
                "error_msg": f'User "{username}" not found.',
                "data": None,
                "msg": None,
            },
        )