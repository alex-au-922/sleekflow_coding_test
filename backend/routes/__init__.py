from fastapi import APIRouter

from .healthcheck import router as healthcheck_router
from .user import router as user_router
from .login import router as login_router

router = APIRouter()
router.include_router(healthcheck_router, prefix="/healthcheck", tags=["healthcheck"])
router.include_router(user_router, prefix="/user", tags=["user"])
router.include_router(login_router, prefix="/login", tags=["login"])

