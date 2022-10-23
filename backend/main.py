import traceback
import uvicorn
import uvloop
from config.project_config import BACKEND_CONFIG
from config.version_config import __version__
from fastapi import FastAPI, status, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from util.exceptions import InvalidTokenError, TokenExpiredError, UnauthorizedError, NotFoundError, InternalServerError, InvalidCredentialsError
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
async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ValidationError",
            "error_msg": str(exc),
            "data": None,
            "msg": None,
        },
    )

@app.middleware("http")
async def error_handler(request: Request, call_next) -> JSONResponse:
    try:
        return await call_next(request)
    except UnauthorizedError as e:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": UnauthorizedError.__name__,
                "error_msg": "Unauthorized action.",
                "data": None,
                "msg": None,
            },
        )
    except TokenExpiredError as e:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": TokenExpiredError.__name__,
                "error_msg": "Token has expired.",
                "data": None,
                "msg": None,
            },
        )
    except InvalidTokenError as e:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": InvalidTokenError.__name__,
                "error_msg": "Invalid token.",
                "data": None,
                "msg": None,
            },
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": InternalServerError.__name__,
                "error_msg": str(e),
                "data": None,
                "msg": None,
            },
        )

if __name__ == "__main__":
    uvloop.install()
    uvicorn.run(app=app, host=BACKEND_CONFIG.host, port=BACKEND_CONFIG.port)
