"""
User router module for the Store API application.
Handles user registration, authentication, and email confirmation.
Provides endpoints for creating user accounts and managing user sessions.
"""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from storeapi import tasks
from storeapi.database import database, user_table
from storeapi.models.user import UserIn
from storeapi.security import (
    authenticate_user,
    create_access_token,
    create_confirmation_token,
    get_password_hash,
    get_subject_for_token_type,
    get_user,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/register", status_code=201)
async def register(user: UserIn, request: Request):
    """
    Register a new user in the system.
    
    Args:
        user: User data including email and password
        request: FastAPI request object to generate confirmation URL
    
    Returns:
        JSON response with registration confirmation message
        
    Raises:
        HTTPException: If a user with the provided email already exists
    """
    if await get_user(user.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )
    hashed_password = get_password_hash(user.password)
    query = user_table.insert().values(email=user.email, password=hashed_password)

    logger.debug(query)

    await database.execute(query)

    confirmation_url = str(
        request.url_for("confirm_email", token=create_confirmation_token(user.email))
    )
    tasks.send_user_registration_email.delay(user.email, confirmation_url)

    return {
        "detail": "User registered successfully. Please confirm your email.",
    }


@router.post("/token")
async def login(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    """
    Authenticate a user and provide an access token.
    
    Args:
        form_data: OAuth2 form containing username (email) and password
    
    Returns:
        JSON response with access token and token type
        
    Raises:
        HTTPException: If authentication fails (handled by authenticate_user)
    """
    user = await authenticate_user(form_data.username, form_data.password)
    access_token = create_access_token(user.email)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/confirm/{token}")
async def confirm_email(token):
    """
    Confirm a user's email address using the provided token.
    
    Args:
        token: Email confirmation token sent to the user
    
    Returns:
        JSON response with confirmation status message
        
    Raises:
        HTTPException: If token is invalid (handled by get_subject_for_token_type)
    """
    email = get_subject_for_token_type(token, "confirmation")
    query = (
        user_table.update().where(user_table.c.email == email).values(confirmed=True)
    )

    logger.debug(query)

    await database.execute(query)
    return {"detail": "User confirmed successfully"}
