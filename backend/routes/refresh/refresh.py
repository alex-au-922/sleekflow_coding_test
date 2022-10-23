from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from datetime import datetime

from .schema import RefreshModel
from util.helper.string import StringHashFactory
from sqlalchemy.exc import NoResultFound # type: ignore
from data_models import DatabaseConnection
from data_models.models import Account, Login
from util.exceptions import NotFoundError, UnauthorizedError, TokenExpiredError, InvalidTokenError
from util.helper.string import StringHashFactory
from util.helper.auth import JWTHandler, RefreshTokenHandler

router = APIRouter()

hasher = StringHashFactory().get_hasher("blake2b")

jwt_handler = JWTHandler()
refresh_token_handler = RefreshTokenHandler()

@router.post("/")
def refresh_refresh_access_tokens(refresh_model: RefreshModel) -> JSONResponse:
    """Refresh the refresh and access tokens"""
    try:
        with DatabaseConnection() as session:
            try:
                user: Account = session.query(Account).filter(Account.username == refresh_model.username).one()
            except NoResultFound:
                raise NotFoundError(f'User "{refresh_model.username}" not found.')
            
            try:
                user_login_info: Login = session.query(Login).filter(Login.user_id == user.user_id).one()
            except NoResultFound:
                raise UnauthorizedError("Unauthorized action.")
            
            if user_login_info.expiry_date < datetime.now():
                raise TokenExpiredError("Refresh token expired.")
            
            if not hasher.verify(string=refresh_model.refresh_token, salt=user_login_info.refresh_token_salt, hash=user_login_info.refresh_token_hash):
                raise InvalidTokenError("Invalid token.")

            access_token = jwt_handler.create_token(username = user.username)
            refresh_token = refresh_token_handler.create_token()
            refresh_token_salt = refresh_token_handler.create_salt()
            refresh_token_hash = hasher.hash(string = refresh_token, salt = refresh_token_salt)
            refresh_token_expiry = refresh_token_handler.get_expiry_time()

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
                "msg": "Refreshed access and refresh tokens.",
            }
        )
    except NotFoundError as e:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": NotFoundError.__name__,
                "error_msg": f'User "{refresh_model.username}" not found.',
                "data": None,
                "msg": None,
            }
        )
    
