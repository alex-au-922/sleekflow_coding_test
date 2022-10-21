from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from .schema import LoginModel
from util.helper.string import StringHashFactory, is_email_format
from sqlalchemy.exc import NoResultFound # type: ignore
from data_models import DatabaseConnection
from data_models.models import Account, Login
from util.exceptions import InvalidCredentialsError
from util.helper.auth import JWTHandler, RefreshTokenHandler
import traceback 

router = APIRouter()

jwt_handler = JWTHandler()
refresh_token_handler = RefreshTokenHandler()

hasher = StringHashFactory().get_hasher("blake2b")

@router.post("/")
def validate_user_login(user_login: LoginModel) -> JSONResponse:
    """Validate a user login."""
    
    try:
        with DatabaseConnection() as session:
            
            user: Account
            if is_email_format(user_login.input_field):
                user = (
                    session
                        .query(Account)
                        .filter_by(
                            email=user_login.input_field
                        ).one()
                )
            else:
                user = (
                    session
                        .query(Account)
                        .filter_by(
                            username=user_login.input_field
                        ).one()
                )
            
            if not hasher.verify(string=user_login.password, salt=user.password_salt, hash=user.password_hash):
                raise InvalidCredentialsError("Invalid credentials.")

            access_token = jwt_handler.create_token(username = user.username)
            refresh_token = refresh_token_handler.create_token()
            refresh_token_salt = refresh_token_handler.create_salt()
            refresh_token_hash = hasher.hash(string = refresh_token, salt = refresh_token_salt)
            refresh_token_expiry = refresh_token_handler.get_expiry_time()

            user_login_info: Login
            user_login_info = session.query(Login).filter_by(user_id=user.user_id).one_or_none()
            if user_login_info is None:
                user_login_info = Login(user_id=user.user_id, refresh_token_hash=refresh_token_hash, refresh_token_salt = refresh_token_salt, expiry_date=refresh_token_expiry)
                session.add(user_login_info)
            else:
                user_login_info.refresh_token_hash = refresh_token_hash
                user_login_info.refresh_token_salt = refresh_token_salt
                user_login_info.expiry_date = refresh_token_expiry
            session.commit()

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "error": None,
                "error_msg": None,
                "data": {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "type": "Bearer",
                    "expires_in": jwt_handler.get_expiry_timestamp(access_token),
                },
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
        traceback.print_exc()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": e.__class__.__name__,
                "error_msg": str(e),
                "data": None,
                "msg": None,
            }
        )