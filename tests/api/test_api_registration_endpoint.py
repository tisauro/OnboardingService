import secrets
from datetime import datetime, timedelta, timezone
from unittest import mock
from unittest.mock import AsyncMock

import pytest

from app.core.db import models
from app.core.schemas import schemas
from app.core.security import get_password_hash, validate_bootstrap_key


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
        assert "Failed to provision device in AWS" in detail
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
    @staticmethod
    async def create_bootstrap_key(
        db_session, is_active=True, days_until_expiry=5
    ) -> tuple[models.BootstrapKey, str]:
        """Helper to create bootstrap key and return (db_key, raw_key)"""
        created_date = datetime.now(timezone.utc)
        expiration_date = created_date + timedelta(days=days_until_expiry)

        raw_key = secrets.token_urlsafe(32)
        key_hash = get_password_hash(raw_key)
        key_hint = raw_key[-4:]

        db_key = models.BootstrapKey(
            key_hash=key_hash,
            key_hint=key_hint,
            key_group="test_group",
            created_date=created_date,
            expiration_date=expiration_date,
            is_active=is_active,
        )
        db_session.add(db_key)
        await db_session.commit()
        return db_key, raw_key

    async def test_registration_device_key_valid(self, db_session):
        _, raw_key = await self.create_bootstrap_key(db_session)
        assert await validate_bootstrap_key(db_session, raw_key)

    async def test_registration_device_key_revoked(self, db_session):
        _, raw_key = await self.create_bootstrap_key(db_session, is_active=False)
        assert not await validate_bootstrap_key(db_session, raw_key)

    async def test_registration_device_key_expired(self, db_session):
        _, raw_key = await self.create_bootstrap_key(db_session, days_until_expiry=-5)
        assert not await validate_bootstrap_key(db_session, raw_key)

    async def test_registration_device_key_expired_and_revoked(self, db_session):
        _, raw_key = await self.create_bootstrap_key(
            db_session, is_active=False, days_until_expiry=-5
        )
        assert not await validate_bootstrap_key(db_session, raw_key)

    async def test_registration_device_key_not_found(self, db_session):
        raw_key = "Not a valid key"
        assert not await validate_bootstrap_key(db_session, raw_key)

    async def test_registration_device_key_wrong_hash(self, db_session):
        _, _ = await self.create_bootstrap_key(db_session)
        wrong_key = secrets.token_urlsafe(32)
        assert not await validate_bootstrap_key(db_session, wrong_key)
