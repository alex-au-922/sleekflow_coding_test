from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from .schema import LoginModel
from util.helper.string import StringHashFactory, is_email_format
from sqlalchemy.exc import NoResultFound # type: ignore
from data_models import DatabaseConnection
from data_models.models import Account
from util.exceptions import InvalidCredentialsError

router = APIRouter()

hasher = StringHashFactory().get_hasher("blake2b")

@router.post("/")
def validate_user_login(user_login: LoginModel) -> JSONResponse:
    """Validate a user login."""
    
    try:
        with DatabaseConnection() as session:
            
            user: Account
            if is_email_format(user_login.input_field):
                user = session.query(Account).filter_by(email=user_login.input_field).one()
            else:
                user = session.query(Account).filter_by(username=user_login.input_field).one()
            
            if not hasher.verify(string=user_login.password, salt=user.password_salt, hash=user.password_hash):
                raise InvalidCredentialsError("Invalid credentials.")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "error": None,
                "error_msg": None,
                "data": None,
                "msg": 'Login successful.',
            }
        )

    except (NoResultFound, InvalidCredentialsError) as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": InvalidCredentialsError.__name__,
                "error_msg": "Invalid credentials.",
                "data": None,
                "msg": None,
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": e.__class__.__name__,
                "error_msg": str(e),
                "data": None,
                "msg": None,
            }
        )