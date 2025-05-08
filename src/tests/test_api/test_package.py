# src/tests/test_api/test_package.py
import pytest
from http import HTTPStatus
from fastapi.testclient import TestClient
from sqlalchemy import text

# удобный хелпер из conftest.py
from src.tests.conftest import unwrap


# ───────────────────────── positive flow ──────────────────────────
@pytest.mark.asyncio
async def test_create_package(test_client: TestClient, create_package_type):
    type_id = create_package_type("Electronics")

    body = {
        "name": "Test Package",
        "weight": 1.5,
        "content_cost_usd": 100.0,
        "type_id": type_id,
    }
    resp = test_client.post("/packages", json=body)

    assert resp.status_code == HTTPStatus.CREATED
    data = unwrap(resp)

    assert data["name"] == body["name"]
    assert data["weight"] == body["weight"]
    assert data["content_cost_usd"] == body["content_cost_usd"]
    assert data["type_id"] == body["type_id"]
    assert data["delivery_cost_rub"] is None
    assert "id" in data


# ───────────────────────── get‑package (Не рассчитано) ─────────────────────────
@pytest.mark.asyncio
async def test_get_package_not_calculated(test_client: TestClient, create_package_type):
    type_id = create_package_type("Clothing")
    body = {
        "name": "Clothes",
        "weight": 0.8,
        "content_cost_usd": 50,
        "type_id": type_id,
    }
    pkg_id = unwrap(test_client.post("/packages", json=body))["id"]

    resp = test_client.get(f"/packages/{pkg_id}")
    assert resp.status_code == HTTPStatus.OK
    payload = unwrap(resp)  # {"message": "Не рассчитано"}
    assert payload["message"] == "Не рассчитано"


# ───────────────────────── get‑package (есть delivery_cost) ─────────────────────
@pytest.mark.asyncio
async def test_get_package_with_calculated_delivery(
    test_client: TestClient, create_package_type, async_session
):
    type_id = create_package_type("Clothing")
    body = {
        "name": "Clothes",
        "weight": 0.8,
        "content_cost_usd": 50,
        "type_id": type_id,
    }
    pkg_id = unwrap(test_client.post("/packages", json=body))["id"]

    # правим вручную delivery_cost_rub
    await async_session.execute(
        text("UPDATE packages SET delivery_cost_rub = :c WHERE id = :i"),
        {"c": 500.0, "i": pkg_id},
    )
    await async_session.commit()

    resp = test_client.get(f"/packages/{pkg_id}")
    assert resp.status_code == HTTPStatus.OK
    data = unwrap(resp)

    assert data["name"] == body["name"]
    assert data["delivery_cost_rub"] == 500.0


# ───────────────────────── not‑found ─────────────────────────────
@pytest.mark.asyncio
async def test_get_package_not_found(test_client: TestClient):
    resp = test_client.get("/packages/99999")
    assert resp.status_code == HTTPStatus.NOT_FOUND
    # при ошибках success=False и поле message
    assert resp.json()["message"] == "Package not found"


# ───────────────────────── список + пагинация + фильтр ────────────
@pytest.mark.parametrize(
    "page,page_size,flt,expect",
    [
        (1, 10, None, 3),
        (1, 2, None, 2),
        (2, 2, None, 1),
        (1, 10, "type1", 1),  # Books
        (1, 10, "type2", 2),  # Gadgets
    ],
)
@pytest.mark.asyncio
async def test_get_packages_with_filter(
    test_client: TestClient, create_package_type, page, page_size, flt, expect
):
    t1 = create_package_type("Books")  # «type1»
    t2 = create_package_type("Gadgets")  # «type2»

    seed = [
        {"name": "Book", "weight": 1.2, "content_cost_usd": 30, "type_id": t1},
        {"name": "G1", "weight": 2.5, "content_cost_usd": 200, "type_id": t2},
        {"name": "G2", "weight": 3.1, "content_cost_usd": 300, "type_id": t2},
    ]
    for row in seed:
        test_client.post("/packages", json=row)

    qs = f"/packages?page={page}&page_size={page_size}"
    if flt == "type1":
        qs += f"&type_id={t1}"
    elif flt == "type2":
        qs += f"&type_id={t2}"

    r = test_client.get(qs)
    assert r.status_code == HTTPStatus.OK
    assert len(unwrap(r)) == expect


# ───────────────────────── валидационные / бизнес‑ошибки ──────────
@pytest.mark.asyncio
async def test_register_package_validation_errors(
    test_client: TestClient, create_package_type
):
    tid = create_package_type("Valid")

    # pydantic‑ошибки → 422
    bad_pydantic = [
        {"name": "neg weight", "weight": -1, "content_cost_usd": 10, "type_id": tid},
        {"name": "zero cost", "weight": 1, "content_cost_usd": 0, "type_id": tid},
    ]
    for body in bad_pydantic:
        assert (
            test_client.post("/packages", json=body).status_code
            == HTTPStatus.UNPROCESSABLE_ENTITY
        )

    # business‑валидация → 400
    r = test_client.post(
        "/packages",
        json={"name": "bad type", "weight": 1, "content_cost_usd": 10, "type_id": 9999},
    )
    assert r.status_code == HTTPStatus.BAD_REQUEST
