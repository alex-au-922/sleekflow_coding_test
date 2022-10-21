from types import TracebackType
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from config.database_config import DATABASE_CONFIG
from typing import Final, Optional, Type, final

DB_CONN_URL = "postgresql://{}:{}@{}:{}/{}".format(
    DATABASE_CONFIG.user,
    DATABASE_CONFIG.password,
    DATABASE_CONFIG.host,
    DATABASE_CONFIG.port,
    DATABASE_CONFIG.database
)

Engine: Final = create_engine(DB_CONN_URL)
SessionLocal: Final = sessionmaker(autocommit=False, autoflush=False, bind=Engine, expire_on_commit=False)

Base: Final = declarative_base()

@final
class DatabaseConnection:
    def __init__(self) -> None:
        self.__session = SessionLocal()

    def __enter__(self) -> Session:
        return self.__session

    def __exit__(
        self, 
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException], 
        exc_tb: Optional[TracebackType]
    ) -> bool:
        self.__session.close()
        return exc_type is None