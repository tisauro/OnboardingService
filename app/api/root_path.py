import logging

from fastapi import APIRouter

logger = logging.getLogger(__name__)

base_router = APIRouter()


@base_router.get("/ping")
async def ping() -> dict[str, str]:
    """
    Health check endpoint do not remove
    used by the load balance to check app is alive
    """
    logger.debug("Pong!")
    return {"ping": "pong"}
