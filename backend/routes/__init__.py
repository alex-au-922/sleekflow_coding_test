from fastapi import APIRouter

from .healthcheck import router as healthcheck_router
from .user import router as user_router

router = APIRouter()
router.include_router(healthcheck_router, prefix="/healthcheck", tags=["healthcheck"])
router.include_router(user_router, prefix="/user", tags=["user"])

