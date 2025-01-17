from typing import Callable, List

import httpx
import pytest
from pydantic import EmailStr

from server.application.auth.queries import GetAccountByEmail
from server.application.organizations.views import OrganizationView
from server.config.di import resolve
from server.domain.auth.exceptions import AccountDoesNotExist
from server.domain.common.types import id_factory
from server.domain.organizations.types import Siret
from server.seedwork.application.messages import MessageBus

from ..factories import CreateOrganizationFactory, fake
from ..helpers import TestPasswordUser


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload_factory, expected_errors_attrs",
    [
        pytest.param(
            lambda _: {},
            [
                {"loc": ["body", "organization_siret"], "type": "value_error.missing"},
                {"loc": ["body", "email"], "type": "value_error.missing"},
                {"loc": ["body", "password"], "type": "value_error.missing"},
            ],
            id="empty",
        ),
        pytest.param(
            lambda siret: {
                "organization_siret": siret,
                "email": "john",
                "password": "s3kr3t",
            },
            [{"type": "value_error.email"}],
            id="invalid-email-no-domain",
        ),
        pytest.param(
            lambda siret: {
                "organization_siret": siret,
                "email": "john@doe",
                "password": "s3kr3t",
            },
            [{"type": "value_error.email"}],
            id="invalid-email-no-domain-extension",
        ),
        pytest.param(
            lambda siret: {
                "organization_siret": siret,
                "email": "johndoe.com",
                "password": "s3kr3t",
            },
            [{"type": "value_error.email"}],
            id="invalid-email-no-@",
        ),
        pytest.param(
            lambda siret: {
                "organization_siret": siret,
                "email": "john@",
                "password": "s3kr3t",
            },
            [{"type": "value_error.email"}],
            id="invalid-email-no-suffix",
        ),
        pytest.param(
            lambda siret: {
                "organization_siret": siret,
                "email": "@doe.com",
                "password": "s3kr3t",
            },
            [{"type": "value_error.email"}],
            id="invalid-email-no-prefix",
        ),
    ],
)
async def test_create_user_invalid(
    client: httpx.AsyncClient,
    temp_org: OrganizationView,
    admin_user: TestPasswordUser,
    payload_factory: Callable[[Siret], dict],
    expected_errors_attrs: List[dict],
) -> None:
    payload = payload_factory(temp_org.siret)
    response = await client.post("/auth/users/", json=payload, auth=admin_user.auth)
    assert response.status_code == 422

    data = response.json()
    assert len(data["detail"]) == len(expected_errors_attrs)

    for error, expected_error_attrs in zip(data["detail"], expected_errors_attrs):
        error_attrs = {key: error[key] for key in expected_error_attrs}
        assert error_attrs == expected_error_attrs


@pytest.mark.asyncio
async def test_create_user(
    client: httpx.AsyncClient,
    temp_org: OrganizationView,
    temp_user: TestPasswordUser,
    admin_user: TestPasswordUser,
) -> None:
    payload = {
        "organization_siret": str(temp_org.siret),
        "email": "john@doe.com",
        "password": "s3kr3t",
    }

    # Permissions
    response = await client.post("/auth/users/", json=payload)
    assert response.status_code == 401
    response = await client.post("/auth/users/", json=payload, auth=temp_user.auth)
    assert response.status_code == 403

    response = await client.post("/auth/users/", json=payload, auth=admin_user.auth)
    assert response.status_code == 201
    user = response.json()
    id_ = user["id"]
    assert isinstance(id_, str)
    assert user == {
        "id": id_,
        "organization_siret": str(temp_org.siret),
        "email": "john@doe.com",
        "role": "USER",
    }


@pytest.mark.asyncio
async def test_create_user_already_exists(
    client: httpx.AsyncClient, temp_user: TestPasswordUser, admin_user: TestPasswordUser
) -> None:
    bus = resolve(MessageBus)
    # Doesn't have to be in the same organization. Only email matters.
    siret = await bus.execute(CreateOrganizationFactory.build())

    payload = {
        "organization_siret": str(siret),
        "email": temp_user.account.email,
        "password": "somethingelse",
    }
    response = await client.post("/auth/users/", json=payload, auth=admin_user.auth)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_user_org_does_not_exist(
    client: httpx.AsyncClient, admin_user: TestPasswordUser
) -> None:
    payload = {
        "organization_siret": fake.siret(),
        "email": "john@doe.com",
        "password": "somethingelse",
    }
    response = await client.post("/auth/users/", json=payload, auth=admin_user.auth)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_login(client: httpx.AsyncClient, temp_user: TestPasswordUser) -> None:
    payload = {"email": temp_user.account.email, "password": temp_user.password}
    response = await client.post("/auth/login/", json=payload)
    assert response.status_code == 200
    user = response.json()
    assert user == {
        "id": str(temp_user.account_id),
        "organization_siret": str(temp_user.account.organization_siret),
        "email": temp_user.account.email,
        "role": temp_user.account.role.value,
        "api_token": temp_user.account.api_token,
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "email, password",
    [
        pytest.param("bad@mydomain.org", "{password}", id="bad-email"),
        pytest.param("{email}", "badpass", id="bad-password"),
    ],
)
async def test_login_failed(
    client: httpx.AsyncClient, email: str, password: str, temp_user: TestPasswordUser
) -> None:
    payload = {
        "email": email.format(email=temp_user.account.email),
        "password": password.format(password=temp_user.password),
    }
    response = await client.post("/auth/login/", json=payload)
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Invalid credentials"


@pytest.mark.asyncio
async def test_get_connected_user(
    client: httpx.AsyncClient, temp_user: TestPasswordUser
) -> None:
    response = await client.get("/auth/users/me/", auth=temp_user.auth)
    assert response.status_code == 200
    assert response.json() == {
        "id": str(temp_user.account_id),
        "organization_siret": str(temp_user.account.organization_siret),
        "email": temp_user.account.email,
        "role": temp_user.account.role.value,
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "headers",
    [
        pytest.param({}, id="missing-header"),
        pytest.param({"Authorization": ""}, id="empty-header"),
        pytest.param({"Authorization": "{api_token}"}, id="missing-scheme"),
        pytest.param({"Authorization": "NotBearer {api_token}"}, id="bad-scheme"),
        pytest.param({"Authorization": "Bearer badtoken"}, id="bad-token"),
    ],
)
async def test_get_connected_user_failed(
    client: httpx.AsyncClient, temp_user: TestPasswordUser, headers: dict
) -> None:
    if "Authorization" in headers:
        headers["Authorization"] = headers["Authorization"].format(
            api_token=temp_user.account.api_token
        )

    response = await client.get("/auth/users/me/", headers=headers)
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Invalid credentials"


@pytest.mark.asyncio
async def test_delete_user(
    client: httpx.AsyncClient, temp_user: TestPasswordUser, admin_user: TestPasswordUser
) -> None:
    bus = resolve(MessageBus)

    # Permissions
    response = await client.delete(f"/auth/users/{temp_user.account_id}/")
    assert response.status_code == 401
    response = await client.delete(
        f"/auth/users/{temp_user.account_id}/", auth=temp_user.auth
    )
    assert response.status_code == 403

    response = await client.delete(
        f"/auth/users/{temp_user.account_id}/", auth=admin_user.auth
    )
    assert response.status_code == 204

    query = GetAccountByEmail(email=EmailStr(temp_user.account.email))
    with pytest.raises(AccountDoesNotExist):
        await bus.execute(query)


@pytest.mark.asyncio
async def test_delete_user_idempotent(
    client: httpx.AsyncClient, admin_user: TestPasswordUser
) -> None:
    # Represents a non-existing user, or a user previously deleted.
    # These should be handled the same way as existing users by
    # this endpoint (idempotency).
    user_id = id_factory()

    response = await client.delete(f"/auth/users/{user_id}/", auth=admin_user.auth)
    assert response.status_code == 204
