"""
Tasks module for the Store API application.
This module defines Celery tasks for asynchronous processing,
including email sending and image generation features.
"""
import logging
from typing import Dict, Optional, Any

import httpx
import sqlalchemy

from storeapi.celery_app import celery_app
from storeapi.config import config
from storeapi.database import post_table

logger = logging.getLogger(__name__)


class APIResponseError(Exception):
    """
    Exception raised when an API request fails.
    Provides information about HTTP status codes and error details.
    """


@celery_app.task
def send_simple_email(to: str, subject: str, body: str):
    """
    Send a simple email using Mailgun API.
    """
    logger.debug("Sending email", extra={"to": to, "subject": subject})

    try:
        with httpx.Client() as client:  # A synchronous Client is used in Celery tasks
            response = client.post(
                f"https://api.mailgun.net/v3/{config.MAILGUN_DOMAIN}/messages",
                auth=("api", config.MAILGUN_API_KEY),
                data={
                    "from": f"David Toscano <postmaster@{config.MAILGUN_DOMAIN}>",
                    "to": [to],
                    "subject": subject,
                    "text": body,
                },
            )
            response.raise_for_status()
            logger.debug("%s", response.content)
            return True
    except httpx.HTTPStatusError as err:
        logger.error("API request failed: %s", err)
        raise APIResponseError(
            f"API request failed with status code {err.response.status_code}"
        ) from err


@celery_app.task
def send_user_registration_email(email: str, confirmation_url: str):
    """
    Send a user registration email.
    """
    return send_simple_email(
        email,
        "Successfully signed up",
        (
            f"Hi {email}! You have successfully signed up to the Stores REST API."
            " Please confirm your email by clicking on the"
            f" following link: {confirmation_url}"
        ),
    )


@celery_app.task()
def _generate_image_api(prompt: str) -> Dict[str, str]:
    """
    Generate an image using Pollinations.ai API (no API key required).
    """
    logger.debug("Generating image with prompt: %s...", prompt[:50])

    # If we're in test mode, return a sample URL
    if config.ENV_STATE == "test":
        logger.warning("Using test mode for image generation")
        return {"output_url": "https://example.com/test-image.jpg"}

    try:
        # Shorten this line to avoid line too long
        pollinations_params = "?width=1024&height=1024&seed=42&model=flux"

        # Build the URL with prompt and parameters
        pollinations_url = f"https://pollinations.ai/p/{prompt}{pollinations_params}"

        # The Pollinations API works differently - it returns the image directly
        # not a JSON with the URL, so we need to build the URL ourselves
        image_url = pollinations_url

        logger.info("Image URL generated: %s", image_url)

        # Return a dictionary compatible with existing code
        return {"output_url": image_url}

    except httpx.HTTPStatusError as err:
        logger.error("API request failed: %s", err)
        raise APIResponseError(
            f"API request failed with status code {err.response.status_code}"
        ) from err
    except httpx.RequestError as err:
        logger.error("Connection error: %s", err)
        raise APIResponseError(f"Connection error: {str(err)}") from err


@celery_app.task
def generate_image_and_add_to_post(
        email: str,
        post_id: str,
        post_url: str,
        database_url: str,
        prompt: str = "A blue british shorthair cat is sitting on a couch",
) -> Optional[Dict[str, Any]]:
    """
    Generate an image and add it to the post.
    Simplified version without retry logic.
    """
    logger.info(
        "Generating image for post #%s",
        post_id,
        extra={"post_id": post_id, "email": email, "prompt_sample": prompt[:30]},
    )

    # Check idempotence: verify if the post already has an image
    try:
        engine = sqlalchemy.create_engine(database_url)
        with engine.connect() as connection:
            result = connection.execute(
                sqlalchemy.select(post_table.c.image_url).where(
                    post_table.c.id == post_id
                )
            ).fetchone()

            if result and result[0]:
                logger.info("Post #%s already has an image: %s", post_id, result[0])
                send_simple_email.delay(
                    email,
                    "Image generation completed",
                    (
                        f"Hi {email}! Your image has been generated and added to your post."
                        f" Please click on the following link to view it: {post_url}"
                    ),
                )
                return {"output_url": result[0], "status": "already_processed"}
    except sqlalchemy.exc.SQLAlchemyError as e:
        logger.error("Error checking post image: %s", str(e))
        # If we can't verify, continue with image generation

    try:
        # Generate image
        response = _generate_image_api(prompt)
        image_url = response["output_url"]

        # Update the database in a transaction
        engine = sqlalchemy.create_engine(database_url)
        with engine.begin() as connection:  # start transaction
            query = (
                post_table.update()
                .where(post_table.c.id == post_id)
                .values(image_url=image_url)
            )
            connection.execute(query)
            logger.info("Post #%s updated with image: %s", post_id, image_url)

        # Send success email
        send_simple_email.delay(
            email,
            "Image generation completed",
            (
                f"Hi {email}! Your image has been generated and added to your post."
                f" Please click on the following link to view it: {post_url}"
            ),
        )

        return {"output_url": image_url, "status": "success"}

    except APIResponseError as err:
        logger.error("Error generating image: %s", str(err))
        send_simple_email.delay(
            email,
            "Error generating image",
            (
                f"Hi {email}! There was an error generating an image for"
                " your post. Please try again later."
            ),
        )
    except (
            sqlalchemy.exc.SQLAlchemyError,
            httpx.TransportError,
            httpx.TimeoutException,
            KeyError,
            IndexError,
    ) as e:
        # Capture specific errors instead of a generic Exception
        logger.error("Unexpected error: %s", str(e))
        send_simple_email.delay(
            email,
            "Error processing your request",
            (
                f"Hi {email}! There was an unexpected error processing your image"
                " request. Our team has been notified and is working on it."
            ),
        )

    return None
