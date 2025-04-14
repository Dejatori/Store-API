"""
Security module test suite.
Tests the functionality of token creation, authentication, password hashing,
and user validation for the Store API application.
"""
import time

import pytest
from jose import jwt

from storeapi import security


def test_access_token_expire_minutes():
    """Test that access tokens are set to expire after 30 minutes."""
    assert security.access_token_expire_minutes() == 30


def test_confirm_token_expire_minutes():
    """Test that confirmation tokens are set to expire after 1440 minutes (24 hours)."""
    assert security.confirm_token_expire_minutes() == 1440


@pytest.mark.parametrize(
    "create_token_func,token_type",
    [
        (security.create_access_token, "access"),
        (security.create_confirmation_token, "confirmation"),
    ],
)
def test_create_token(create_token_func, token_type):
    """
    Test that tokens are created with correct subject and type.
    
    Args:
        create_token_func: Function that creates the token
        token_type: Expected type of the token
    """
    token = create_token_func("123")
    assert {"sub": "123", "type": token_type}.items() <= jwt.decode(
        token, key=security.SECRET_KEY, algorithms=[security.ALGORITHM]
    ).items()


@pytest.mark.parametrize(
    "create_token_func,token_type",
    [
        (security.create_access_token, "access"),
        (security.create_confirmation_token, "confirmation"),
    ],
)
def test_get_subject_for_token_type_valid_confirmation(create_token_func, token_type):
    """
    Test that token subject can be extracted correctly.
    
    Args:
        create_token_func: Function that creates the token
        token_type: Type of the token to validate
    """
    email = "test@example.com"
    token = create_token_func(email)

    assert security.get_subject_for_token_type(token, token_type)


def test_get_subject_for_token_expired(mocker):
    """Test that expired tokens are rejected with appropriate error message."""
    mocker.patch("storeapi.security.access_token_expire_minutes", return_value=-1)
    email = "test@example.com"
    token = security.create_access_token(email)

    with pytest.raises(security.HTTPException) as exc_info:
        security.get_subject_for_token_type(token, "access")

    assert "Token has expired" in str(exc_info.value.detail)


def test_get_subject_for_token_invalid():
    """Test that invalid tokens are rejected with appropriate error message."""
    token = "invalid token"
    with pytest.raises(security.HTTPException) as exc_info:
        security.get_subject_for_token_type(token, "access")

    assert "Invalid token" in str(exc_info.value.detail)


def test_get_subject_for_token_type_missing_sub():
    """Test that tokens missing the subject field are rejected."""
    exp = int(time.time()) + 3600
    payload = {"exp": exp, "type": "access"}
    token = jwt.encode(payload, key=security.SECRET_KEY, algorithm=security.ALGORITHM)

    with pytest.raises(security.HTTPException) as exc_info:
        security.get_subject_for_token_type(token, "access")

    assert "Token is missing 'sub' field" in str(exc_info.value.detail)


def test_get_subject_for_token_type_wrong_type():
    """Test that tokens with incorrect type are rejected."""
    email = "test@example.com"
    token = security.create_confirmation_token(email)

    with pytest.raises(security.HTTPException) as exc_info:
        security.get_subject_for_token_type(token, "access")

    assert "Token type is invalid" in str(exc_info.value.detail)


def test_password_hashes():
    """Test that password hashing and verification work correctly."""
    password = "password123"
    assert security.verify_password(password, security.get_password_hash(password))


@pytest.mark.anyio
async def test_get_user(registered_user_fixture: dict):
    """
    Test that a registered user can be retrieved from the database.
    
    Args:
        registered_user_fixture: Test user data
    """
    user = await security.get_user(registered_user_fixture["email"])

    assert user.email == registered_user_fixture["email"]


@pytest.mark.anyio
async def test_get_user_not_found():
    """Test that get_user returns None for non-existent users."""
    user = await security.get_user("not_found@example.com")
    assert user is None


@pytest.mark.anyio
async def test_authenticate_user(confirmed_user_fixture: dict):
    """
    Test that a confirmed user can be authenticated with correct credentials.
    
    Args:
        confirmed_user_fixture: Test user data with confirmed status
    """
    user = await security.authenticate_user(
        confirmed_user_fixture["email"], confirmed_user_fixture["password"]
    )
    assert user.email == confirmed_user_fixture["email"]


@pytest.mark.anyio
async def test_authenticate_user_not_found():
    """Test that authentication fails for non-existent users."""
    with pytest.raises(security.HTTPException):
        await security.authenticate_user("test@example.net", "1234")


@pytest.mark.anyio
async def test_authenticate_user_wrong_password(confirmed_user_fixture: dict):
    """
    Test that authentication fails with incorrect password.
    
    Args:
        confirmed_user_fixture: Test user data with confirmed status
    """
    with pytest.raises(security.HTTPException):
        await security.authenticate_user(confirmed_user_fixture["email"], "wrong_password")


@pytest.mark.anyio
async def test_get_current_user(confirmed_user_fixture: dict):
    """
    Test that current user can be retrieved from a valid token.
    
    Args:
        confirmed_user_fixture: Test user data with confirmed status
    """
    token = security.create_access_token(confirmed_user_fixture["email"])
    user = await security.get_current_user(token)
    assert user.email == confirmed_user_fixture["email"]


@pytest.mark.anyio
async def test_get_current_user_invalid_token():
    """Test that get_current_user fails with invalid token."""
    with pytest.raises(security.HTTPException):
        await security.get_current_user("invalid_token")


@pytest.mark.anyio
async def test_get_current_user_wrong_type_token(confirmed_user_fixture: dict):
    """
    Test that get_current_user fails with wrong token type.
    
    Args:
        confirmed_user_fixture: Test user data with confirmed status
    """
    token = security.create_confirmation_token(confirmed_user_fixture["email"])
    with pytest.raises(security.HTTPException):
        await security.get_current_user(token)
