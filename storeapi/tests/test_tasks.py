"""
Task module test suite.
Tests email sending, image generation, and task processing functionality
for the Store API application's asynchronous tasks.
"""
from unittest.mock import MagicMock, patch

import httpx
import pytest
from pytest import fixture

from storeapi.tasks import (
    APIResponseError,
    _generate_image_api,
    generate_image_and_add_to_post,
    send_simple_email,
    send_user_registration_email,
)


@fixture
def mock_http_error_response():
    """Fixture that provides a simulated HTTP 500 error response."""
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Error",
        request=httpx.Request("POST", "//"),
        response=httpx.Response(500, request=httpx.Request("POST", "//")),
    )
    mock_response.status_code = 500
    return mock_response


def test_send_simple_email():
    """Test that send_simple_email works correctly"""
    with patch("httpx.Client") as mock_client:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.status_code = 200

        mock_client.return_value.__enter__.return_value.post.return_value = (
            mock_response
        )

        result = send_simple_email("test@example.net", "Test Subject", "Test Body")
        assert result is True
        mock_client.return_value.__enter__.return_value.post.assert_called_once()


def test_send_simple_email_api_error():
    """Test that send_simple_email handles API errors correctly"""
    with patch("httpx.Client") as mock_client:
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Error",
            request=httpx.Request("POST", "//"),
            response=httpx.Response(500, request=httpx.Request("POST", "//")),
        )
        mock_response.status_code = 500

        mock_client.return_value.__enter__.return_value.post.return_value = (
            mock_response
        )

        with pytest.raises(APIResponseError):
            send_simple_email("test@example.net", "Test Subject", "Test Body")


def test_send_user_registration_email():
    """Test that send_user_registration_email works correctly"""
    with patch("storeapi.tasks.send_simple_email") as mock_send_email:
        mock_send_email.return_value = True

        result = send_user_registration_email(
            "test@example.net", "http://confirm/token"
        )

        mock_send_email.assert_called_once()
        call_args = mock_send_email.call_args[0]
        assert call_args[0] == "test@example.net"
        assert call_args[1] == "Successfully signed up"
        assert "Hi test@example.net" in call_args[2]
        assert "http://confirm/token" in call_args[2]
        assert result is True


def test_generate_image_api_success():
    """Test that verifies _generate_image_api works properly with Pollinations.ai"""
    with patch("storeapi.config.config") as mock_config:
        # Simulate not being in test mode
        mock_config.ENV_STATE = "dev"

        prompt = "A cute cat"
        expected_url = (
            f"https://pollinations.ai/p/{prompt}?width=1024&height=1024&seed=42&model=flux"
        )

        # No need to mock HTTP client as we no longer make API calls
        # The URL is generated directly
        result = _generate_image_api(prompt)

        assert result == {"output_url": expected_url}


@patch("storeapi.tasks._generate_image_api")
@patch("storeapi.tasks.send_simple_email")
@patch("sqlalchemy.create_engine")
def test_generate_image_and_add_to_post_success(
        mock_create_engine, mock_send_email, mock_generate_image
):
    """Test that verifies generate_image_and_add_to_post works properly"""
    # Configure mocks
    mock_response = {
        "output_url": (
            "https://pollinations.ai/p/A%20cute%20cat?width=1024&height=1024&seed=42&model=flux"
        )
    }
    mock_generate_image.return_value = mock_response
    mock_send_email.delay.return_value = True

    # Mock for SQLAlchemy engine and connection
    mock_engine = MagicMock()
    mock_create_engine.return_value = mock_engine
    mock_connection = MagicMock()
    mock_engine.begin.return_value.__enter__.return_value = mock_connection
    mock_engine.connect.return_value.__enter__.return_value = mock_connection

    # Simulate that the post has no image
    mock_result = MagicMock()
    mock_result.fetchone.return_value = (None,)
    mock_connection.execute.return_value = mock_result

    # Custom prompt for the test
    custom_prompt = "A cute cat sitting on a chair"

    # Call the function
    result = generate_image_and_add_to_post(
        "test@example.com",
        "1",
        "posts/1",
        "sqlite:///test.db",
        custom_prompt,
    )

    # Assertions
    mock_generate_image.assert_called_once_with(custom_prompt)
    mock_connection.execute.assert_called()
    mock_send_email.delay.assert_called_once()
    assert result == {"output_url": mock_response["output_url"], "status": "success"}


@patch("storeapi.tasks._generate_image_api")
@patch("storeapi.tasks.send_simple_email")
@patch("sqlalchemy.create_engine")
def test_generate_image_and_add_to_post_with_existing_image(
        mock_create_engine, mock_send_email, mock_generate_image
):
    """Test that verifies if the post already has an image, no new one is generated"""
    # generate_image_api should not be called
    mock_generate_image.return_value = None
    mock_send_email.delay.return_value = True

    # Mock for SQLAlchemy engine and connection
    mock_engine = MagicMock()
    mock_create_engine.return_value = mock_engine
    mock_connection = MagicMock()
    mock_engine.connect.return_value.__enter__.return_value = mock_connection

    # Simulate that the post already has an image
    existing_image_url = "https://example.com/existing-image.jpg"
    mock_result = MagicMock()
    mock_result.fetchone.return_value = (existing_image_url,)
    mock_connection.execute.return_value = mock_result

    # Call the function
    result = generate_image_and_add_to_post(
        "test@example.com",
        "1",
        "posts/1",
        "sqlite:///test.db",
        "A cute cat",
    )

    # Assertions
    mock_generate_image.assert_not_called()
    mock_send_email.delay.assert_called_once()
    assert result == {"output_url": existing_image_url, "status": "already_processed"}


@patch("storeapi.tasks._generate_image_api")
@patch("storeapi.tasks.send_simple_email")
@patch("sqlalchemy.create_engine")
def test_generate_image_and_add_to_post_api_error(
        mock_create_engine, mock_send_email, mock_generate_image
):
    """Test that verifies API error handling"""
    # Configure mocks
    mock_generate_image.side_effect = APIResponseError("API error")
    mock_send_email.delay.return_value = True

    # Mock for SQLAlchemy engine and connection
    mock_engine = MagicMock()
    mock_create_engine.return_value = mock_engine
    mock_connection = MagicMock()
    mock_engine.connect.return_value.__enter__.return_value = mock_connection

    # Simulate that the post has no image
    mock_result = MagicMock()
    mock_result.fetchone.return_value = (None,)
    mock_connection.execute.return_value = mock_result

    # Call the function
    result = generate_image_and_add_to_post(
        "test@example.com",
        "1",
        "posts/1",
        "sqlite:///test.db",
        "A cute cat",
    )

    # Assertions
    mock_generate_image.assert_called_once()
    call_template = (
        "Hi test@example.com! There was an error generating an image for your post. "
        "Please try again later."
    )
    mock_send_email.delay.assert_called_once_with(
        "test@example.com",
        "Error generating image",
        call_template,
    )
    assert result is None
