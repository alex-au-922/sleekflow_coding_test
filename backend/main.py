import uvicorn
import uvloop
from config.project_config import BACKEND_CONFIG
from config.version_config import __version__
from fastapi import FastAPI
from data_models import Base, Engine

app = FastAPI(title="SleekFlow TODOs API Coding Test", version=__version__)

@app.on_event("startup")
def startup() -> None:
    Base.metadata.drop_all(bind = Engine)
    Base.metadata.create_all(bind = Engine)

if __name__ == "__main__":
    uvloop.install()
    uvicorn.run(app=app, host=BACKEND_CONFIG.host, port=BACKEND_CONFIG.port)
