from typing import Annotated, TypedDict

from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.database import SessionLocal


# Dependency
async def get_db():
    """
    FastAPI dependency to get a database session.
    """
    async with SessionLocal() as db:
        yield db


# Type alias for cleaner annotations
SessionDep = Annotated[AsyncSession, Depends(get_db)]


class PaginationParams(TypedDict):
    skip: int
    limit: int


# Pagination helper
# we can explicitly define the type of skip parameter as Query with default
def pagination_params(
    skip: int = Query(default=0, ge=0), limit: int = Query(default=10, ge=1, le=100)
) -> PaginationParams:
    """Common pagination parameters"""
    return {"skip": skip, "limit": limit}


PaginationDep = Annotated[PaginationParams, Depends(pagination_params)]
