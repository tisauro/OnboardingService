import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core import aws_iot_client, security
from app.core.schemas import schemas
from app.core.settings import Settings, get_settings

# ==============================================================================
# Public Endpoint: Device Provisioning
# ==============================================================================
registration_router = APIRouter()

api_key_header = APIKeyHeader(name="X-Api-Key", description="The device's unique bootstrap API key")

logger = logging.getLogger(__name__)


@registration_router.post(
    "/register",
    response_model=schemas.DeviceProvisionResponse,
    tags=["Device Provisioning"],
    summary="Public: Device registers itself using a bootstrap key.",
)
async def register_device(
    registration_data: schemas.DeviceRegistrationRequest,
    x_api_key: str = Depends(api_key_header),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """
    This public endpoint is hit by a device on its first boot.

    The device provides its factory-installed bootstrap key in the
    `x-api-key` header and its desired `device_id` in the body.

    If the key is valid, the service will:
    1.  Provision a new X.509 certificate from AWS IoT Core.
    2.  Create an IoT Thing with the `device_id`.
    3.  Attach the certificate to the Thing.
    4.  Attach the default IoT Policy to the certificate.
    5.  Return the new certificate and private key to the device.
    """

    db_key = await security.validate_bootstrap_key(db, x_api_key)

    if not db_key:
        logger.warning(
            "Device registration failed: invalid bootstrap key for device_id=%s",
            registration_data.device_id,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired bootstrap key."
        )

    try:
        provision_data = await aws_iot_client.provision_device(
            device_id=registration_data.device_id, policy_name=settings.IOT_POLICY_NAME
        )
        logger.warning(
            "Device registration failed: invalid bootstrap key for device_id=%s",
            registration_data.device_id,
        )
    except Exception as e:
        logger.exception(f"Failed to provision device: {str(e)}")
        # Catch potential AWS errors (e.g., Thing already exists, policy not found)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to provision device in AWS",
        )
    return provision_data
