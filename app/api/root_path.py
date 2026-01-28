import logging

from fastapi import APIRouter

logger = logging.getLogger("uvicorn")

base_router = APIRouter()


@base_router.get("/ping")
async def ping() -> dict:
    """
    Health check endpoint do not remove
    used by the load balance to check app is alive
    """
    logger.info("Pong!")
    return {"ping": "pong"}
