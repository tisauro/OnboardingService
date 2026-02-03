import random
import string

import pytest
from datetime import datetime, timedelta, timezone
from app.core.db.models import BootstrapKey


@pytest.mark.asyncio
@pytest.mark.parametrize("skip,limit", [(-1, 10), (0, -1), (0, 0), (0, 101)])
async def test_list_keys_rejects_invalid_pagination(client, skip, limit):
    resp = await client.get("/private/v1/admin/keys", params={"skip": skip, "limit": limit})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_delete_key_not_found(client):
    resp = await client.delete("/private/v1/admin/keys/9999")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Key not found"


@pytest.mark.asyncio
class TestCreateKeyValidation:
    @pytest.mark.parametrize("days", [-1, 0, 366])
    async def test_create_key_validation_error(self, client, days):
        resp = await client.post("/private/v1/admin/keys", json={"group": "test", "expires_in_days": days})
        assert resp.status_code == 422

    async def test_create_key_validation_default(self, client):
        resp = await client.post("/private/v1/admin/keys", json={"group": "test"})
        assert resp.status_code == 200
        assert resp.json()["expiration_date"] is not None
        created_date = datetime.fromisoformat(resp.json()['created_date'])
        expiration_date = datetime.fromisoformat(resp.json()['expiration_date'])
        delta = expiration_date - created_date
        assert timedelta(days=29, hours=23) <= delta <= timedelta(days=30, hours=1)

    async def test_create_key_validation_valid_value(self, client):
        resp = await client.post("/private/v1/admin/keys", json={"group": "test", "expires_in_days": 10})
        assert resp.status_code == 200
        assert resp.json()["expiration_date"] is not None
        created_date = datetime.fromisoformat(resp.json()['created_date'])
        expiration_date = datetime.fromisoformat(resp.json()['expiration_date'])
        delta = expiration_date - created_date
        assert timedelta(days=9, hours=23) <= delta <= timedelta(days=10, hours=1)


@pytest.mark.asyncio
class TestUpdateKeyEndpoint:
    async def test_update_key_200(self, client):
        # Create a key
        my_key_res = await client.post("/private/v1/admin/keys", json={"group": "test"})
        assert my_key_res.status_code == 200
        assert my_key_res.json()["is_active"] is True
        key_id = my_key_res.json()["id"]
        resp = await client.put(f"/private/v1/admin/keys/{key_id}", json={"activation_flag": False})
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False
        assert resp.json()["id"] == key_id

    async def test_update_key_not_found(self, client):
        resp = await client.put("/private/v1/admin/keys/9999", json={"activation_flag": True})
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Key not found"

    async def test_update_key_expired(self, client, db_session):
        created = datetime.now(tz=timezone.utc) - timedelta(days=31)
        expiration_date = created - timedelta(days=10)
        rnd_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=64))

        bootstrap_key = BootstrapKey(key_hash=rnd_str[:32],
                                     key_hint=rnd_str[:4], group="test",
                                     is_active=False, created_date=created, expiration_date=expiration_date)
        db_session.add(bootstrap_key)
        await db_session.commit()
        await db_session.refresh(bootstrap_key)
        resp = await client.put(f"/private/v1/admin/keys/{bootstrap_key.id}", json={"activation_flag": True})
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Key has expired"

    async def test_update_key_expired_deactivate(self, client, db_session):
        created = datetime.now(tz=timezone.utc) - timedelta(days=31)
        expiration_date = created - timedelta(days=10)
        rnd_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=64))
        bootstrap_key = BootstrapKey(key_hash=rnd_str[:32],
                                     key_hint=rnd_str[:4], group="test",
                                     is_active=True, created_date=created, expiration_date=expiration_date)
        db_session.add(bootstrap_key)
        await db_session.commit()
        await db_session.refresh(bootstrap_key)
        resp = await client.put(f"/private/v1/admin/keys/{bootstrap_key.id}", json={"activation_flag": False})
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False
        assert resp.json()["id"] == bootstrap_key.id
