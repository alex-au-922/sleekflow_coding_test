from tortoise import Tortoise, run_async
from util.database import database_connection


async def main():
    await database_connection()
    await Tortoise.generate_schemas()


if __name__ == "__main__":
    run_async(main())
