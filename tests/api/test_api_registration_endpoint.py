from unittest import mock
from unittest.mock import AsyncMock

import pytest

from app.core.schemas import schemas


@mock.patch("app.api.public.v1.registration.security")
@mock.patch("app.api.public.v1.registration.aws_iot_client")
@pytest.mark.asyncio
class TestRegistrationEndpointApi:
    async def test_register_device_happy_path(self, mocked_iot_client, mocked_security, client):
        device_certs = schemas.DeviceProvisionResponse(
            certificate_pem="fake_pem",
            private_key="fake_key",
            certificate_id="fake_id",
            thing_name="fake_name",
            thing_arn="fake_arn",
        )

        mocked_iot_client.provision_device = AsyncMock(return_value=device_certs)

        mocked_security.validate_bootstrap_key = AsyncMock(return_value=True)
        resp = await client.post(
            "/public/v1/register",
            json={"device_id": "fake_device_id"},
            headers={"X-Api-Key": "fake_api_key"},
        )
        assert resp.status_code == 200
        assert resp.json() == device_certs.model_dump()
        mocked_iot_client.provision_device.assert_called_once_with(
            device_id="fake_device_id", policy_name=mock.ANY
        )
        mocked_security.validate_bootstrap_key.assert_called_once_with(mock.ANY, "fake_api_key")

    async def test_registration_device_invalid_key(
        self, mocked_iot_client, mocked_security, client
    ):
        mocked_security.validate_bootstrap_key = AsyncMock(return_value=False)
        resp = await client.post(
            "/public/v1/register",
            json={"device_id": "fake_device_id"},
            headers={"X-Api-Key": "fake_api_key"},
        )
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Invalid or expired bootstrap key."
        mocked_iot_client.provision_device.assert_not_called()
        mocked_security.validate_bootstrap_key.assert_called_once()
        mocked_security.validate_bootstrap_key.assert_called_once_with(mock.ANY, "fake_api_key")

    async def test_registration_device_iot_client_error(
        self, mocked_iot_client, mocked_security, client
    ):
        mocked_iot_client.provision_device = AsyncMock(side_effect=Exception())

        mocked_security.validate_bootstrap_key = AsyncMock(return_value=True)
        resp = await client.post(
            "/public/v1/register",
            json={"device_id": "fake_device_id"},
            headers={"X-Api-Key": "fake_api_key"},
        )
        assert resp.status_code == 500
        detail = resp.json()["detail"]
        assert "Failed to provision device in AWS:" in detail
        mocked_iot_client.provision_device.assert_called_once()
        mocked_security.validate_bootstrap_key.assert_called_once()
        mocked_iot_client.provision_device.assert_called_once_with(
            device_id="fake_device_id", policy_name=mock.ANY
        )
        mocked_security.validate_bootstrap_key.assert_called_once_with(mock.ANY, "fake_api_key")

    async def test_registration_missing_device_id(self, mocked_iot_client, mocked_security, client):
        mocked_security.validate_bootstrap_key = AsyncMock(return_value=True)
        resp = await client.post(
            "/public/v1/register", json={}, headers={"X-Api-Key": "fake_api_key"}
        )
        assert resp.status_code == 422

    async def test_registration_missing_api_key(self, mocked_iot_client, mocked_security, client):
        resp = await client.post("/public/v1/register", json={"device_id": "fake_device_id"})
        assert resp.status_code == 401


@pytest.mark.asyncio
class TestRegistrationEndpointSecurity:
    async def test_registration_device_key_expired(self, db_session):
        pass

    async def test_registration_device_key_revoked(self, db_session):
        pass

    async def test_registration_device_key_not_found(self, client):
        pass
