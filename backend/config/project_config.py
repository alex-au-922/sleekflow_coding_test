try:
    from dotenv import load_dotenv

    load_dotenv("../.env.dev")
except ImportError:
    pass

import os
from typing import Final


class __BackendConfig:
    def __init__(self) -> None:
        self.__host = os.getenv("BACKEND_HOST", "localhost")
        self.__port = int(os.getenv("BACKEND_PORT", 8080))

    @property
    def host(self) -> str:
        return self.__host

    @property
    def port(self) -> int:
        return self.__port


BACKEND_CONFIG: Final = __BackendConfig()

PROJECT_MODE: Final = os.getenv("PROJECT_MODE", "DEVELOPMENT")
