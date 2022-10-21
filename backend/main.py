import uvicorn
import uvloop
from config.project_config import BACKEND_CONFIG
from config.version_config import __version__
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from .middlewares import validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from data_models import Base, Engine
from routes import router

app = FastAPI(title="SleekFlow TODOs API Coding Test", version=__version__)

#TODO: Change the origins to the frontend URL which is specified in config file
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix = "/api")

@app.exception_handler(RequestValidationError)
async def handle_validation_error(request, exc: RequestValidationError) -> JSONResponse:
    return await validation_exception_handler(request, exc)

if __name__ == "__main__":
    uvloop.install()
    uvicorn.run(app=app, host=BACKEND_CONFIG.host, port=BACKEND_CONFIG.port)
