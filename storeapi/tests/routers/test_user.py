"""
User router test module.
Tests user registration, confirmation, and authentication functionality
for the Store API application.
"""
import pytest
from httpx import AsyncClient, Response


async def register_user(
        async_client_fixture: AsyncClient, email: str, password: str
) -> Response:
    """
    Helper function to register a user.

    Args:
        async_client_fixture: HTTP client for making requests
        email: User's email address
        password: User's password

    Returns:
        Response: HTTP response from the registration endpoint
    """
    return await async_client_fixture.post(
        "/register", json={"email": email, "password": password}
    )


@pytest.mark.anyio
async def test_register_user(async_client_fixture: AsyncClient) -> None:
    """
    Test registering a new user.

    Verifies that a user can be registered successfully and the response
    contains the expected message.
    """
    response = await register_user(async_client_fixture, "test@example.net", "1234")
    assert response.status_code == 201
    assert "User registered successfully" in response.json()["detail"]


@pytest.mark.anyio
async def test_register_user_already_exists(
        async_client_fixture: AsyncClient, registered_user_fixture: dict
) -> None:
    """
    Test registering a user with an email that already exists.

    Verifies that attempting to register with an existing email returns
    a conflict response with the appropriate error message.
    """
    response = await register_user(
        async_client_fixture, registered_user_fixture["email"], "1234"
    )
    assert response.status_code == 409
    assert "A user with this email already exists" in response.json()["detail"]


@pytest.mark.anyio
async def test_confirm_user(async_client_fixture: AsyncClient, mocker):
    """
    Test confirming a user's registration.

    Verifies that a user can confirm their registration by following
    the confirmation URL sent via email.
    """
    spy = mocker.patch("storeapi.tasks.send_user_registration_email.delay")
    await register_user(async_client_fixture, "test@example.net", "1234")

    confirmation_url = str(spy.call_args[0][1])
    response = await async_client_fixture.get(confirmation_url)

    assert response.status_code == 200
    assert "User confirmed successfully" in response.json()["detail"]


@pytest.mark.anyio
async def test_confirm_user_invalid_token(async_client_fixture: AsyncClient):
    """
    Test confirming registration with an invalid token.

    Verifies that an invalid confirmation token is rejected with the
    appropriate error message.
    """
    response = await async_client_fixture.get("/confirm/invalid_token")

    assert response.status_code == 401
    assert "Invalid token" in response.json()["detail"]


@pytest.mark.anyio
async def test_confirm_user_expired_token(async_client_fixture: AsyncClient, mocker):
    """
    Test confirming registration with an expired token.

    Verifies that an expired confirmation token is rejected with the
    appropriate error message.
    """
    mocker.patch("storeapi.security.confirm_token_expire_minutes", return_value=-1)

    spy = mocker.patch("storeapi.tasks.send_user_registration_email.delay")
    await register_user(async_client_fixture, "test@example.net", "1234")

    confirmation_url = str(spy.call_args[0][1])
    response = await async_client_fixture.get(confirmation_url)

    assert response.status_code == 401
    assert "Token has expired" in response.json()["detail"]


@pytest.mark.anyio
async def test_login_user_not_exists(async_client_fixture: AsyncClient) -> None:
    """
    Test logging in with a non-existent user.

    Verifies that attempting to login with a non-existent email returns
    an unauthorized response.
    """
    response = await async_client_fixture.post(
        "/token",
        data={
            "username": "test@example.net",  # OAuth2 uses username, not email
            "password": "1234",
        },
    )
    assert response.status_code == 401


@pytest.mark.anyio
async def test_login_user_not_confirmed(
        async_client_fixture: AsyncClient, registered_user_fixture: dict
) -> None:
    """
    Test logging in with an unconfirmed user.

    Verifies that attempting to login with an unconfirmed account returns
    an unauthorized response with the appropriate error message.
    """
    response = await async_client_fixture.post(
        "/token",
        data={
            "username": registered_user_fixture["email"],  # OAuth2 uses username, not email
            "password": registered_user_fixture["password"],
        },
    )
    assert response.status_code == 401
    assert "User has not confirmed email" in response.json()["detail"]


@pytest.mark.anyio
async def test_login_user(
        async_client_fixture: AsyncClient, confirmed_user_fixture: dict
) -> None:
    """
    Test successful user login.

    Verifies that a confirmed user can log in successfully and receive
    an access token.
    """
    response = await async_client_fixture.post(
        "/token",
        data={
            "username": confirmed_user_fixture["email"],  # OAuth2 uses username, not email
            "password": confirmed_user_fixture["password"],
        },
    )
    assert response.status_code == 200
