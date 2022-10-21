from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from .schemas.user import UpdatePasswordModel, CreateUserModel
from data_models import DatabaseConnection
from data_models.models import Account
from sqlalchemy.exc import IntegrityError
from util.helper.string import StringHashFactory
from typing import Final

router = APIRouter()

hasher: Final = StringHashFactory().get_hasher("blake2b")

@router.post("/")
def create_user(user: CreateUserModel) -> JSONResponse:
    """Create a user."""

    password_hash = hasher.hash(string=user.password, salt=user.password_salt)
    
    try:
        with DatabaseConnection() as session:
            new_user = Account(
                username=user.username,
                email=user.email,
                password_hash=password_hash,
                password_salt=user.password_salt,
            )
            session.add(new_user)
            session.commit()
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "error": None,
                "error_msg": None,
                "data": new_user.user_id,
                "msg": f'User "{user.username}" created successfully.',
            },
        )
    except IntegrityError as e:
        if 'Key (username)' in str(e):
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={
                    "error": "DuplicateError",
                    "error_msg": f'Username "{user.username}" already exists.',
                    "data": None,
                    "msg": None,
                },
            )
        elif 'Key (email)' in str(e):
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={
                    "error": "DuplicateError",
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
                "error": e.__class__.__name__,
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
            if hasher.hash(string = user.old_password,salt = old_password_salt) != query_user.password_hash:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "error": "UnauthenticatedError",
                        "error_msg": "Incorrect old password.",
                        "data": None,
                        "msg": None,
                    },
                )
            
            new_password_hash = hasher.hash(string=user.new_password, salt=user.new_password_salt)
            query_user.password_hash = new_password_hash
            query_user.password_salt = user.new_password_salt
            session.commit()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "error": None,
                "error_msg": None,
                "data": query_user.user_id,
                "msg": "Password updated successfully.",
            },
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": e.__class__.__name__,
                "error_msg": str(e),
                "data": None,
                "msg": None,
            },
        )