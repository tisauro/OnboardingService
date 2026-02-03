import datetime

from pydantic import BaseModel, ConfigDict, Field

# ==============================================================================
# Bootstrap Key Schemas (Admin)
# ==============================================================================


class BootstrapKeyCreateRequest(BaseModel):
    """
    Request body for creating a new bootstrap key.
    """

    group: str | None = None
    expires_in_days: int = Field(default=30, ge=1, le=365)


class BootstrapKeyCreateResponse(BaseModel):
    """
    Response when creating a key. Includes the raw_key *once*.
    """

    id: int
    raw_key: str
    key_hint: str
    group: str | None
    created_date: datetime.datetime
    expiration_date: datetime.datetime
    is_active: bool = True


class BootstrapKeyInfo(BaseModel):
    """
    Schema for listing keys in the admin panel. Excludes sensitive info.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    key_hint: str
    group: str | None
    created_date: datetime.datetime
    expiration_date: datetime.datetime | None
    is_active: bool


class BootstrapKeyUpdateRequest(BaseModel):
    # key_id: int
    activation_flag: bool


# ==============================================================================
# Device Provisioning Schemas (Public)
# ==============================================================================


class DeviceRegistrationRequest(BaseModel):
    """
    Request body for the /register endpoint.
    """

    device_id: str


class DeviceProvisionResponse(BaseModel):
    """
    Response for a successful provisioning request.
    """

    certificate_pem: str
    private_key: str
    certificate_id: str
    thing_name: str
    thing_arn: str


# ==============================================================================
# AWS IoT Device Schemas (Admin)
# ==============================================================================


class IotDevice(BaseModel):
    """
    Represents a device (Thing) registered in AWS IoT Core.
    """

    thing_name: str
    thing_arn: str
    attributes: dict


class RevokeCertificateRequest(BaseModel):
    """
    Request body for revoking a certificate.
    """

    certificate_id: str
