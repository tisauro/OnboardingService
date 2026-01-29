import datetime

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.db import models
from app.core.settings import Settings, get_settings

# Security scheme for admin endpoints
admin_api_key_header = APIKeyHeader(name="x-admin-api-key")

# Password hashing context for bootstrap keys
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """Hashes a password (or bootstrap key)."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


# --- Admin Security ---


def get_admin_api_key(
    api_key: str = Depends(admin_api_key_header), settings: Settings = Depends(get_settings)
) -> str:
    """
    FastAPI dependency that validates the admin API key.
    """
    if api_key == settings.ADMIN_API_KEY:
        return api_key
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing admin API key."
    )


# --- Device Security ---


async def validate_bootstrap_key(db: AsyncSession, key: str) -> models.BootstrapKey | None:
    """
    Validates a device's bootstrap key.

    Iterates through stored hashes to find a match.
    Checks if the key is active and not expired.
    """
    # This is a simple (but not highly performant) way to check against
    # all stored hashes. For a massive fleet, a different lookup
    # (e.g., using a key hint) might be needed, but this is the most secure.

    result = await db.execute(select(models.BootstrapKey).filter(models.BootstrapKey.is_active))
    keys = result.scalars().all()

    for db_key in keys:
        if verify_password(key, db_key.key_hash):
            # Found a match. Now check expiration.
            if db_key.expiration_date and db_key.expiration_date < datetime.datetime.now(
                datetime.timezone.utc
            ):
                # Key is expired
                return None

            # Key is valid, active, and not expired
            return db_key

    # No key matched
    return None
