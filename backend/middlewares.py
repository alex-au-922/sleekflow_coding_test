from fastapi import status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

async def error_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ValidationError",
            "error_msg": str(exc),
            "data": None,
            "msg": None,
        },
    )