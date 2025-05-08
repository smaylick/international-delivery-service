import pytest
from http import HTTPStatus
from fastapi.testclient import TestClient

from src.tests.conftest import unwrap


@pytest.mark.asyncio
async def test_create_package_type(test_client: TestClient):
    body = {"name": "Electronics"}
    resp = test_client.post("/package-types", json=body)

    assert resp.status_code == HTTPStatus.OK
    data = unwrap(resp)
    assert data["name"] == body["name"]
    assert isinstance(data["id"], int)


@pytest.mark.asyncio
async def test_create_duplicate_package_type(test_client: TestClient):
    body = {"name": "Electronics"}

    test_client.post("/package-types", json=body)
    resp2 = test_client.post("/package-types", json=body)
    assert resp2.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.asyncio
async def test_get_package_types(test_client: TestClient):
    test_client.post("/package-types", json={"name": "Electronics"})
    test_client.post("/package-types", json={"name": "Clothing"})

    resp = test_client.get("/package-types")
    assert resp.status_code == HTTPStatus.OK

    items = unwrap(resp)
    assert isinstance(items, list)
    names = {pt["name"] for pt in items}
    assert names == {"Electronics", "Clothing"}
