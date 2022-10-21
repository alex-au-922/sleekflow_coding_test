try:
    from dotenv import load_dotenv

    load_dotenv("../.env.dev")
except ImportError:
    pass

import os
from typing import Final

class __AuthTokensConfig:
    def __init__(self) -> None:
        self.__secret_key = os.getenv("JWT_SECRET_KEY", "secret")
        self.__refresh_token_expiry = int(os.getenv("REFRESH_TOKEN_EXP", 60 * 60 * 24 * 15))
        self.__access_token_expiry = int(os.getenv("ACCESS_TOKEN_EXP", 60 * 15))
        self.__algorithm = os.getenv("JWT_ALGORITHM", "HS256")

    @property
    def secret_key(self) -> str:
        return self.__secret_key

    @property
    def refresh_token_expiry(self) -> int:
        return self.__refresh_token_expiry

    @property
    def access_token_expiry(self) -> int:
        return self.__access_token_expiry
    
    @property
    def algorithm(self) -> str:
        return self.__algorithm

AUTH_TOKENS_CONFIG: Final = __AuthTokensConfig()