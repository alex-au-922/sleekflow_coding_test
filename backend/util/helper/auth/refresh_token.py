from typing import Dict
from datetime import datetime, timedelta
from util.types import Serializable
from util.exceptions import UnauthorizedError, TokenExpiredError
from util.helper.string import random_string
from config.auth_tokens_config import AUTH_TOKENS_CONFIG

class RefreshTokenHandler:
    """A class that handles refresh token operations."""

    __EXPIRES_DELTA = AUTH_TOKENS_CONFIG.refresh_token_expiry

    def create_token(self) -> str:
        """Create an access token."""

        return random_string(32)
    
    def create_salt(self) -> str:
        """Get the salt of the token."""

        return random_string(10)
   
    def get_expiry_time(self) -> datetime:
        """Get the expiry time of the token."""

        return datetime.now() + timedelta(seconds = self.__EXPIRES_DELTA)
    
    def get_expiry_timestamp(self) -> float:
        """Get the expiry time of the token."""

        return (self.get_expiry_time()).timestamp()
    
