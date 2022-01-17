import httpx
import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload, expected_error_attrs",
    [
        pytest.param(
            {},
            {"loc": ["body", "email"], "type": "value_error.missing"},
            id="empty",
        ),
        pytest.param(
            {"email": "john"},
            {"type": "value_error.email"},
            id="invalid-email-no-domain",
        ),
        pytest.param(
            {"email": "john@doe"},
            {"type": "value_error.email"},
            id="invalid-email-no-domain-extension",
        ),
        pytest.param(
            {"email": "johndoe.com"},
            {"type": "value_error.email"},
            id="invalid-email-no-@",
        ),
        pytest.param(
            {"email": "john@"},
            {"type": "value_error.email"},
            id="invalid-email-no-suffix",
        ),
        pytest.param(
            {"email": "@doe.com"},
            {"type": "value_error.email"},
            id="invalid-email-no-prefix",
        ),
    ],
)
async def test_create_user_invalid(
    client: httpx.AsyncClient, payload: dict, expected_error_attrs: dict
) -> None:
    response = await client.post("/auth/users/", json=payload)
    assert response.status_code == 422

    data = response.json()
    assert len(data["detail"]) == 1

    error_attrs = {key: data["detail"][0][key] for key in expected_error_attrs}
    assert error_attrs == expected_error_attrs


@pytest.mark.asyncio
async def test_create_user(client: httpx.AsyncClient) -> None:
    response = await client.post("/auth/users/", json={"email": "john@doe.com"})
    assert response.status_code == 201
    data = response.json()
    assert isinstance(data.pop("id"), int)
    assert data == {"email": "john@doe.com"}


@pytest.mark.asyncio
async def test_create_user_already_exists(client: httpx.AsyncClient) -> None:
    response = await client.post("/auth/users/", json={"email": "john@doe.com"})
    assert response.status_code == 400


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "headers, status_code",
    [
        pytest.param(
            {},
            403,
            id="empty",
        ),
        pytest.param(
            {"X-Email": "gibberish"},
            403,
            id="invalid-email",
        ),
        pytest.param(
            {"X-Email": "doesnotexist@example.com"},
            403,
            id="user-does-not-exist",
        ),
        pytest.param(
            {"X-Email-Other": "john@doe.com"},
            403,
            id="wrong-scheme",
        ),
        pytest.param(
            {"X-Email": "john@doe.com"},
            200,
            id="valid",
        ),
        pytest.param(
            {"x-email": "john@doe.com"},
            200,
            id="valid-case-insensitive",
        ),
    ],
)
async def test_check_auth(
    client: httpx.AsyncClient, headers: dict, status_code: int
) -> None:
    response = await client.get("/auth/check/", headers=headers)

    assert response.status_code == status_code

    if status_code == 200:
        assert response.json() == {"is_authenticated": True}