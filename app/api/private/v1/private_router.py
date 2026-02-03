import logging

from fastapi import APIRouter

from app.api.private.v1.bootstrap_keys import boostrap_key_router
from app.api.private.v1.device_management import device_management_router

logger = logging.getLogger("uvicorn")

private_router = APIRouter()

private_router.include_router(boostrap_key_router)
private_router.include_router(device_management_router)
