import uvicorn
import uvloop
from config.model_config import MODEL_PATH
from config.project_config import BACKEND_CONFIG
from config.version_config import __version__
from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise
from util.database import DB_CONN_URL

app = FastAPI(title="SleekFlow TODOs API Coding Test", version=__version__)


@app.on_event("startup")
def startup_event() -> None:
    register_tortoise(
        app,
        db_url=DB_CONN_URL,
        modules={"models": [MODEL_PATH]},
        generate_schemas=True,
        add_exception_handlers=True,
    )


if __name__ == "__main__":
    uvloop.install()
    uvicorn.run(app=app, host=BACKEND_CONFIG.host, port=BACKEND_CONFIG.port)
