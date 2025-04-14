"""
Pytest configuration file for the Store API test suite.
Defines fixtures for test client setup, database connections, user management,
and mocks for testing the application without external dependencies.
"""
import os
from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

# Set environment to test before importing app modules
os.environ["ENV_STATE"] = "test"

# Import app modules after setting environment
# pylint: disable=wrong-import-position
from storeapi.database import database, user_table  # noqa: E402
from storeapi.main import app  # noqa: E402


@pytest.fixture(scope="session")
def anyio_backend():
    """
    Configure pytest-anyio to use asyncio backend for async tests.

    Returns:
        str: The name of the backend to use
    """
    return "asyncio"


@pytest.fixture()
def client_fixture() -> Generator:
    """
    Create a test client for the FastAPI application.

    Yields:
        TestClient: A FastAPI test client
    """
    yield TestClient(app)


@pytest.fixture(autouse=True)
async def db() -> AsyncGenerator:
    """
    Set up and tear down the database connection for each test.
    This fixture runs automatically for all tests.

    Yields:
        None: Just establishes and closes database connection
    """
    await database.connect()
    yield
    await database.disconnect()


# pylint: disable=redefined-outer-name
@pytest.fixture()
async def async_client_fixture(client_fixture) -> AsyncGenerator:
    """
    Create an async HTTP client for testing async endpoints.

    Args:
        client_fixture: The standard test client

    Yields:
        AsyncClient: An async capable HTTP client
    """
    async with AsyncClient(
            transport=ASGITransport(app=app), base_url=client_fixture.base_url
    ) as ac:
        yield ac


@pytest.fixture()
async def registered_user_fixture(async_client_fixture: AsyncClient) -> dict:
    """
    Create a registered but unconfirmed test user.

    Args:
        async_client_fixture: The async HTTP client

    Returns:
        dict: User details including email, password and ID
    """
    user_details = {"email": "test@example.net", "password": "1234"}
    await async_client_fixture.post("/register", json=user_details)
    query = user_table.select().where(user_table.c.email == user_details["email"])
    user = await database.fetch_one(query)
    user_details["id"] = user.id
    return user_details


@pytest.fixture()
async def confirmed_user_fixture(registered_user_fixture: dict) -> dict:
    """
    Create a confirmed test user by updating a registered user's status.

    Args:
        registered_user_fixture: The registered user details

    Returns:
        dict: User details with confirmed status
    """
    query = (
        user_table.update()
        .where(user_table.c.email == registered_user_fixture["email"])
        .values(confirmed=True)
    )
    await database.execute(query)
    return registered_user_fixture


@pytest.fixture()
async def logged_in_token_fixture(
        async_client_fixture: AsyncClient, confirmed_user_fixture: dict
) -> str:
    """
    Obtain an authentication token for a confirmed user.

    Args:
        async_client_fixture: The async HTTP client
        confirmed_user_fixture: The confirmed user details

    Returns:
        str: Authentication token for the user
    """
    response = await async_client_fixture.post(
        "/token",
        data={
            "username": confirmed_user_fixture["email"],  # OAuth2 uses username by convention
            "password": confirmed_user_fixture["password"],
        },
    )
    return response.json()["access_token"]


@pytest.fixture(autouse=True)
def mock_celery_tasks_fixture(mocker):
    """
    Mock celery tasks to avoid actual execution during tests.

    Args:
        mocker: pytest-mock fixture

    Returns:
        MagicMock: The mocked task
    """
    return mocker.patch("storeapi.tasks.send_user_registration_email.delay")
