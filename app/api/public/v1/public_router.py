from fastapi import APIRouter
import logging

from app.api.public.v1.registration import registration_router

logger = logging.getLogger("uvicorn")

public_router = APIRouter()

public_router.include_router(registration_router)