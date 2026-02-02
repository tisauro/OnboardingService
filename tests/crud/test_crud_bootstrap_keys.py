from unittest.mock import AsyncMock

import pytest
from sqlalchemy.future import select

from app.core.crud import bootstrap_keys
from app.core.crud.bootstrap_keys import BootstrapKeyNotFoundError, delete_key, update_key_status
from app.core.db import models
from app.core.schemas import schemas
from app.core.schemas.schemas import BootstrapKeyUpdateRequest


@pytest.mark.asyncio
class TestBootstrapKeyCRUD:
    async def test_create_key(self, db_session):
        key_data = schemas.BootstrapKeyCreateRequest(group="test-group", expires_in_days=10)
        db_key, raw_key = await bootstrap_keys.create_key(db_session, key_data)

        assert db_key.id is not None
        assert db_key.group == "test-group"
        assert len(raw_key) > 30
        assert db_key.key_hint == raw_key[-4:]
        assert db_key.is_active is True

        # Verify it's in DB
        result = await db_session.execute(
            select(models.BootstrapKey).where(models.BootstrapKey.id == db_key.id)
        )
        stored_key = result.scalar_one_or_none()
        assert stored_key is not None
        assert stored_key.group == "test-group"

    async def test_get_keys(self, db_session):
        # Create some keys first
        for i in range(3):
            key_data = schemas.BootstrapKeyCreateRequest(group=f"group-{i}")
            await bootstrap_keys.create_key(db_session, key_data)

        pagination = {"skip": 0, "limit": 10}
        keys = await bootstrap_keys.get_keys(db_session, pagination)

        assert len(keys) >= 3
        assert all(isinstance(k, models.BootstrapKey) for k in keys)

    async def test_update_key_status(self, db_session):
        # Create a key
        key_data = schemas.BootstrapKeyCreateRequest(group="update-test")
        db_key, _ = await bootstrap_keys.create_key(db_session, key_data)

        # Deactivate it
        update_req = schemas.BootstrapKeyUpdateRequest(activation_flag=False)
        updated_key = await bootstrap_keys.update_key_status(db_key.id, update_req, db_session)

        assert updated_key.is_active is False

        # Reactivate it
        update_req.activation_flag = True
        updated_key = await bootstrap_keys.update_key_status(db_key.id, update_req, db_session)
        assert updated_key.is_active is True

    async def test_update_key_status_not_found(self, db_session):
        update_req = schemas.BootstrapKeyUpdateRequest(activation_flag=False)
        with pytest.raises(BootstrapKeyNotFoundError):
            await bootstrap_keys.update_key_status(9999, update_req, db_session)

    async def test_delete_key(self, db_session):
        # Create a key
        key_data = schemas.BootstrapKeyCreateRequest(group="delete-test")
        db_key, _ = await bootstrap_keys.create_key(db_session, key_data)

        # Delete it
        await bootstrap_keys.delete_key(db_key.id, db_session)

        # Verify it's gone
        result = await db_session.execute(
            select(models.BootstrapKey).where(models.BootstrapKey.id == db_key.id)
        )
        stored_key = result.scalar_one_or_none()
        assert stored_key is None

    async def test_delete_key_not_found(self, db_session):
        with pytest.raises(BootstrapKeyNotFoundError):
            await bootstrap_keys.delete_key(9999, db_session)


@pytest.mark.asyncio
class TestBootstrapKeyCRUDPagination:
    async def test_pagination_contract(self, db_session, seed_bootstrap_keys_20):
        pagination = {"skip": 0, "limit": 10}
        keys1 = await bootstrap_keys.get_keys(db_session, pagination)
        ids1 = [keys.id for keys in keys1]
        pagination = {"skip": 10, "limit": 10}
        keys2 = await bootstrap_keys.get_keys(db_session, pagination)
        ids2 = [key.id for key in keys2]

        assert len(keys1) == 10
        assert len(keys2) == 10
        assert ids1 == sorted(ids1, reverse=True)
        assert ids2 == sorted(ids2, reverse=True)
        assert set(ids1).isdisjoint(set(ids2))
        assert ids1[-1] > ids2[0]  # (desc order continuity check)


@pytest.mark.asyncio
class TestBootstrapKeyCRUDLogic:
    async def test_update_key_status_success(self):
        # Mock DB session
        db = AsyncMock()

        # Mock existing key
        mock_key = models.BootstrapKey(id=1, is_active=True)
        db.get.return_value = mock_key

        # Request data
        update_request = BootstrapKeyUpdateRequest(activation_flag=False)

        # Call function
        result = await update_key_status(1,update_request, db)

        # Verify
        assert result.is_active is False
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(mock_key)
        assert result == mock_key

    async def test_update_key_status_not_found(self):
        db = AsyncMock()
        db.get.return_value = None

        update_request = BootstrapKeyUpdateRequest(activation_flag=False)

        with pytest.raises(BootstrapKeyNotFoundError):
            await update_key_status(1, update_request, db)


@pytest.mark.asyncio
class TestBootstrapKeyCRUDNotFound:
    async def test_delete_key_not_found(self, db_session):
        with pytest.raises(BootstrapKeyNotFoundError):
            await delete_key(9999, db_session)

    async def test_update_key_not_found(self, db_session):
        with pytest.raises(BootstrapKeyNotFoundError):
            key_status = schemas.BootstrapKeyUpdateRequest(activation_flag=False)
            await update_key_status(9999, key_status, db_session)
