import datetime
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


async def create_key(
    db: AsyncSession, key_data: schemas.BootstrapKeyCreateRequest
) -> tuple[models.BootstrapKey, str]:
    if key_data.expires_in_days:
        expires_in_days = key_data.expires_in_days
    else:
        expires_in_days = 30

    expiration_date = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        days=expires_in_days
    )

    raw_key = secrets.token_urlsafe(32)
    key_hash = security.get_password_hash(raw_key)
    key_hint = raw_key[-4:]

    db_key = models.BootstrapKey(
        key_hash=key_hash, key_hint=key_hint, group=key_data.group, expiration_date=expiration_date
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
    db_key.is_active = key_status.activation_flag
    await db.commit()
    await db.refresh(db_key)
    return db_key
