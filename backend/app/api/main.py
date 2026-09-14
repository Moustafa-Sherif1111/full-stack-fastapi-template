from fastapi import APIRouter

from app.api.routes import items, login, private, tags, users, utils
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)
api_router.include_router(tags.router)  # v1.1.0: tag management


if settings.FASTAPI_ENV == "development":
    api_router.include_router(private.router)
