from typing import Annotated, TypedDict

from fastapi import Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.database import SessionLocal


# Dependency
async def get_db():
    """
    FastAPI dependency to get a database session.
    """
    async with SessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()


# Type alias for cleaner annotations
SessionDep = Annotated[AsyncSession, Depends(get_db)]


# Pagination helper
# we can explicitly define the type of skip parameter as Query with default
# value 0 and maximum value 5
def pagination_params(
    skip: int = Query(default=0, qe=0), limit: int = Query(100, ge=1, le=100)
) -> dict:
    """Common pagination parameters"""
    return {"skip": skip, "limit": limit}


class PaginationParams(TypedDict):
    skip: int
    limit: int


PaginationDep = Annotated[PaginationParams, Depends(pagination_params)]


# if we store resources in app_state, access them via dependencies: see context manager in main.py
def get_redis(request: Request):
    """Dependency to get Redis from app state"""
    return request.app.state.redis
