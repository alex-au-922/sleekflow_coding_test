from config.database_config import DATABASE_CONFIG
from tortoise import Tortoise

DB_CONN_URL = "postgres://{}:{}@{}:{}/{}".format(
    DATABASE_CONFIG.user,
    DATABASE_CONFIG.password,
    DATABASE_CONFIG.host,
    DATABASE_CONFIG.port,
    DATABASE_CONFIG.database,
)


async def database_connection() -> None:
    """Initialize database connection"""

    await Tortoise.init(db_url=DB_CONN_URL, modules={"models": ["models"]})
