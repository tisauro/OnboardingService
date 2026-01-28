import datetime
import secrets
from fastapi import Depends, APIRouter, Header, HTTPException, Security, status
from sqlalchemy.orm import Session
from app.core.schemas import schemas
from app.core.db.database import get_db
from app.core import aws_iot_client, security
from app.core.db import models

# ==============================================================================
# Private Endpoints: Admin Management
# ==============================================================================

boostrap_key_router = APIRouter()

admin_api_key = Security(security.get_admin_api_key)


@boostrap_key_router.post(
    "/admin/keys",
    response_model=schemas.BootstrapKeyCreateResponse,
    tags=["Admin"],
    summary="Admin: Create a new bootstrap key."
)
def create_bootstrap_key(
        key_data: schemas.BootstrapKeyCreateRequest,
        db: Session = Depends(get_db),
        admin_key: str = admin_api_key
):
    """
    Creates one or more new bootstrap keys.

    - `key`: A new, secure key is generated automatically.
    - `key_hash`: A hash of the key is stored in the DB.
    - `key_hint`: The last 4 chars of the key are stored for identification.

    **The raw key is returned *only* at creation time.** It cannot be
    retrieved later.
    """
    raw_key = secrets.token_urlsafe(32)
    key_hash = security.get_password_hash(raw_key)
    key_hint = raw_key[-4:]

    expiration_date = None
    if key_data.expires_in_days:
        expiration_date = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
            days=key_data.expires_in_days)

    db_key = models.BootstrapKey(
        key_hash=key_hash,
        key_hint=key_hint,
        group=key_data.group,
        expiration_date=expiration_date
    )
    db.add(db_key)
    db.commit()
    db.refresh(db_key)

    return schemas.BootstrapKeyCreateResponse(
        id=db_key.id,
        raw_key=raw_key,  # Return the raw key this one time
        key_hint=db_key.key_hint,
        group=db_key.group,
        created_date=db_key.created_date,
        expiration_date=db_key.expiration_date
    )


@boostrap_key_router.get(
    "/admin/keys",
    response_model=list[schemas.BootstrapKeyInfo],
    tags=["Admin"],
    summary="Admin: List all bootstrap keys."
)
def list_bootstrap_keys(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db),
        admin_key: str = admin_api_key
):
    """
    Lists all bootstrap keys in the database.
    Does *not* return the raw key or hash.
    """
    keys = db.query(models.BootstrapKey).offset(skip).limit(limit).all()
    return keys


@boostrap_key_router.delete(
    "/admin/keys/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Admin"],
    summary="Admin: Delete a bootstrap key."
)
def delete_bootstrap_key(
        key_id: int,
        db: Session = Depends(get_db),
        admin_key: str = admin_api_key
):
    """
    Deletes a bootstrap key from the database by its ID.
    This permanently revokes the key.
    """
    db_key = db.query(models.BootstrapKey).filter(models.BootstrapKey.id == key_id).first()
    if not db_key:
        raise HTTPException(status_code=404, detail="Key not found")

    db.delete(db_key)
    db.commit()
    return None


@boostrap_key_router.get(
    "/admin/devices",
    response_model=list[schemas.IotDevice],
    tags=["Admin"],
    summary="Admin: List provisioned devices from AWS IoT Core."
)
async def list_iot_devices(admin_key: str = admin_api_key):
    """
    Acts as a proxy to AWS IoT Core to list all registered Things (devices).
    """
    try:
        devices = await aws_iot_client.list_provisioned_devices()
        return devices
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list devices from AWS: {str(e)}"
        )


@boostrap_key_router.post(
    "/admin/devices/revoke",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Admin"],
    summary="Admin: Revoke a device's certificate in AWS IoT Core."
)
async def revoke_iot_certificate(
        revoke_request: schemas.RevokeCertificateRequest,
        admin_key: str = admin_api_key
):
    """
    Revokes a device's certificate in AWS IoT Core.
    This permanently blocks the device from authenticating with the ALB.
    """
    try:
        await aws_iot_client.revoke_device_certificate(
            certificate_id=revoke_request.certificate_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke certificate: {str(e)}"
        )
    return None
