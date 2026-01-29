from app.core import aws_iot_client
from app.core.schemas import schemas
from fastapi import APIRouter, Depends, HTTPException, status

device_management_router = APIRouter()

@device_management_router.get(
    "/admin/devices",
    response_model=list[schemas.IotDevice],
    tags=["Admin"],
    summary="Admin: List provisioned devices from AWS IoT Core.",
)
async def list_iot_devices():
    """
    Acts as a proxy to AWS IoT Core to list all registered Things (devices).
    """
    try:
        devices = await aws_iot_client.list_provisioned_devices()
        return devices
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list devices from AWS: {str(e)}",
        )


@device_management_router.post(
    "/admin/devices/revoke",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Admin"],
    summary="Admin: Revoke a device's certificate in AWS IoT Core.",
)
async def revoke_iot_certificate(
    revoke_request: schemas.RevokeCertificateRequest
):
    """
    Revokes a device's certificate in AWS IoT Core.
    This permanently blocks the device from authenticating with the ALB.
    """
    try:
        await aws_iot_client.revoke_device_certificate(certificate_id=revoke_request.certificate_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke certificate: {str(e)}",
        )
    return None