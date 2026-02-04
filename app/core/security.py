import datetime

from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.db import models

# Password hashing context for bootstrap keys
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """Hashes a password (or bootstrap key)."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


# --- Device Security ---


async def validate_bootstrap_key(db: AsyncSession, key: str) -> bool:
    """
    Validates a device's bootstrap key.

    Iterates through stored hashes to find a match.
    Checks if the key is active and not expired.
    """

    result = await db.execute(
        select(models.BootstrapKey)
        .filter(models.BootstrapKey.is_active)
        .filter(models.BootstrapKey.key_hint == key[-4:])
    )
    keys = result.scalars().all()

    for db_key in keys:
        if verify_password(key, db_key.key_hash):
            # Found a match. Now check expiration.
            if db_key.expiration_date and db_key.expiration_date < datetime.datetime.now(
                datetime.timezone.utc
            ):
                # Key is expired
                return False

            # Key is valid, active, and not expired
            return True

    # No key matched
    return False
