from fastapi import APIRouter
from app.api.private.v1.bootstrap_keys import boostrap_key_router
import logging

logger = logging.getLogger("uvicorn")

private_router = APIRouter()

private_router.include_router(boostrap_key_router)