try:
    from dotenv import load_dotenv

    load_dotenv("../.env.dev")
except ImportError:
    pass

import os
from typing import Final


class __DatabaseConfig:
    def __init__(self) -> None:
        self.__host = os.getenv("DATABASE_HOST", "localhost")
        self.__port = int(os.getenv("DATABASE_PORT", 5432))
        self.__user = os.getenv("DATABASE_USER", "postgres")
        self.__password = os.getenv("DATABASE_PASSWORD", "postgres")
        self.__database = os.getenv("DATABASE_NAME", "postgres")

    @property
    def host(self) -> str:
        return self.__host

    @property
    def port(self) -> int:
        return self.__port

    @property
    def user(self) -> str:
        return self.__user

    @property
    def password(self) -> str:
        return self.__password

    @property
    def database(self) -> str:
        return self.__database


DATABASE_CONFIG: Final = __DatabaseConfig()
