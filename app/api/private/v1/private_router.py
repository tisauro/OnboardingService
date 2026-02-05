from fastapi import APIRouter

from app.api.private.v1.bootstrap_keys import bootstrap_key_router
from app.api.private.v1.device_management import device_management_router

private_router = APIRouter()

private_router.include_router(bootstrap_key_router)
private_router.include_router(device_management_router)
