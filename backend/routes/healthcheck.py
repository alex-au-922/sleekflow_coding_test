from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
router = APIRouter()

@router.get("/")
async def healthcheck() -> JSONResponse:
    """Healthcheck endpoint."""
    
    return JSONResponse(
        content = {
            "msg": "OK",
            "data": None,
            "error": None,
            "error_msg": None,
        },
        status_code=status.HTTP_200_OK
    )