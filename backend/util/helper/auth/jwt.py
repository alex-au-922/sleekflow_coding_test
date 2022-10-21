import jwt # type: ignore
from jwt.exceptions import ExpiredSignatureError, InvalidKeyError # type: ignore
from typing import Dict
from datetime import datetime, timedelta
from util.types import Serializable
from util.exceptions import UnauthorizedError, TokenExpiredError
from config.auth_tokens_config import AUTH_TOKENS_CONFIG

class JWTHandler:
    """A class that handles JWT operations."""

    __SECRET_KEY = AUTH_TOKENS_CONFIG.secret_key
    __ALGORITHM = AUTH_TOKENS_CONFIG.algorithm
    __EXPIRES_DELTA = AUTH_TOKENS_CONFIG.access_token_expiry
    
    def __update_payload(self, payload: Dict[str, Serializable]) -> Dict[str, Serializable]:
        """Update the payload with the expiry time."""

        new_payload = {
            **payload,
            "exp": datetime.now() + timedelta(seconds = self.__EXPIRES_DELTA)
        }
        return new_payload

    def create_token(self, **kwargs: Serializable) -> str:
        """Create an json web token."""

        return jwt.encode(
            self.__update_payload(kwargs), 
            self.__SECRET_KEY, 
            algorithm=self.__ALGORITHM
        )
    
    def get_expiry_time(self, token: str) -> datetime:
        """Get the expiry time of the token."""

        return datetime.fromtimestamp(self.get_expiry_timestamp(token))

    def get_expiry_timestamp(self, token: str) -> float:
        """Get the expiry time of the token."""

        return self.get_payload(token)["exp"]

    def get_payload(self, token: str) -> Dict[str, Serializable]:
        """Decode the token into a payload."""
        try:
            return jwt.decode(
                token, 
                self.__SECRET_KEY, 
                algorithms=[self.__ALGORITHM]
            )
        except ExpiredSignatureError:
            raise TokenExpiredError("Token has expired.")
        except InvalidKeyError:
            raise UnauthorizedError("Invalid token.")