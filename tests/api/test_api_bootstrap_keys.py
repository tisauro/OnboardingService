import pytest


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
async def test_update_key_not_found(client):
    resp = await client.put("/private/v1/admin/keys/9999", json={"activation_flag": True})
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Key not found"
