from datetime import datetime, timezone, timedelta
import secrets

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.deps import PaginationDep
from app.core import security
from app.core.db import models
from app.core.schemas import schemas
from app.core.schemas.schemas import BootstrapKeyUpdateRequest


class BootstrapKeyNotFoundError(Exception):
    pass


class BootstrapKeyExpiredError(Exception):
    pass


async def create_key(
        db: AsyncSession, key_data: schemas.BootstrapKeyCreateRequest
) -> tuple[models.BootstrapKey, str]:
    expires_in_days = key_data.expires_in_days
    created_date = datetime.now(timezone.utc)
    expiration_date = created_date + timedelta(
        days=expires_in_days
    )

    raw_key = secrets.token_urlsafe(32)
    key_hash = security.get_password_hash(raw_key)
    key_hint = raw_key[-4:]

    db_key = models.BootstrapKey(
        key_hash=key_hash, key_hint=key_hint, group=key_data.group, created_date=created_date,
        expiration_date=expiration_date
    )
    db.add(db_key)
    await db.commit()
    return db_key, raw_key


async def get_keys(db: AsyncSession, pagination: PaginationDep):
    result = await db.execute(
        select(models.BootstrapKey)
        .order_by(models.BootstrapKey.id.desc())
        .offset(pagination["skip"])
        .limit(pagination["limit"])
    )
    keys = result.scalars().all()
    return keys


async def delete_key(key_id: int, db: AsyncSession) -> None:
    result = await db.execute(delete(models.BootstrapKey).where(models.BootstrapKey.id == key_id))
    if result.rowcount == 0:
        raise BootstrapKeyNotFoundError(f"Key with id {key_id} not found")

    await db.commit()


async def update_key_status(
        key_id: int, key_status: BootstrapKeyUpdateRequest, db: AsyncSession
) -> models.BootstrapKey:
    db_key = await db.get(models.BootstrapKey, key_id)
    if not db_key:
        raise BootstrapKeyNotFoundError(f"Key with id {key_id} not found")

    now = datetime.now(timezone.utc)
    if db_key.expiration_date is not None and db_key.expiration_date  < now and key_status.activation_flag:
        raise BootstrapKeyExpiredError(f"Key with id {key_id} has expired")
    db_key.is_active = key_status.activation_flag
    await db.commit()
    await db.refresh(db_key)
    return db_key
