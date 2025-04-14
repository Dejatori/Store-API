"""
Main FastAPI application module for the Store API.
This module configures and initializes the FastAPI application with its routes and middleware.
"""
import logging
from contextlib import asynccontextmanager

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI, HTTPException
from fastapi.exception_handlers import http_exception_handler
import sentry_sdk

from storeapi.config import config
from storeapi.database import database
from storeapi.logging_conf import configure_logging
from storeapi.routers.post import router as posts_router
from storeapi.routers.upload import router as upload_router
from storeapi.routers.user import router as users_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app_instance: FastAPI): # pylint: disable=unused-argument
    """
    Manages the startup and shutdown events of the FastAPI application.
    Connects to the database on startup and disconnects on shutdown.

    Args:
        app_instance: The FastAPI application instance (required by FastAPI)
    """
    configure_logging()
    logger.info("Starting FastAPI application")
    await database.connect()
    yield
    await database.disconnect()


sentry_sdk.init(
    dsn=config.SENTRY_DSN,
    # Add data like request headers and IP for users,
    # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
    send_default_pii=True,
)

app = FastAPI(lifespan=lifespan)

app.add_middleware(CorrelationIdMiddleware)
app.include_router(posts_router)
app.include_router(upload_router)
app.include_router(users_router)


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request, exc):
    """
    Custom exception handler for HTTP exceptions.
    Logs the exception details and then delegates to the default handler.
    
    Args:
        request: The request that caused the exception
        exc: The HTTP exception that was raised
        
    Returns:
        The response from the default HTTP exception handler
    """
    logger.error("HTTP Exception: %s, %s", exc.status_code, exc.detail)
    return await http_exception_handler(request, exc)
