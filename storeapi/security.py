"""
Security module for the Store API application.
This module handles authentication, authorization, and token management
including JWT generation, password hashing, and user verification.
"""
import datetime
import logging
from typing import Annotated, Literal

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext

from storeapi.database import database, user_table

logger = logging.getLogger(__name__)

SECRET_KEY = "YtcZBBQ05bp4g2iYHLPlhTTfcV1yZJryiNK3Ry1ixMg="
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"])


def create_credentials_exception(detail: str) -> HTTPException:
    """
    Create a standardized HTTP 401 exception for authentication failures.
    
    Args:
        detail: Specific error message explaining why authentication failed
        
    Returns:
        HTTPException: Properly formatted 401 Unauthorized exception
    """
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def access_token_expire_minutes() -> int:
    """
    Get the expiration time in minutes for access tokens.
    
    Returns:
        int: Number of minutes until access tokens expire
    """
    return 30


def confirm_token_expire_minutes() -> int:
    """
    Get the expiration time in minutes for confirmation tokens.
    
    Returns:
        int: Number of minutes until confirmation tokens expire (24 hours)
    """
    return 60 * 24  # 1 day


def create_access_token(email: str) -> str:
    """
    Create a JWT access token for the specified user.
    
    Args:
        email: User's email address to encode in the token
        
    Returns:
        str: Encoded JWT token with user email and expiration time
    """
    logger.debug("Creating access token", extra={"email": email})
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=access_token_expire_minutes()
    )
    jwt_data = {"sub": email, "exp": expire, "type": "access"}
    encoded_jwt = jwt.encode(jwt_data, key=SECRET_KEY, algorithm=ALGORITHM)
    logger.debug("Access token created")
    return encoded_jwt


def create_confirmation_token(email: str) -> str:
    """
    Create a JWT confirmation token for email verification.
    
    Args:
        email: User's email address to encode in the token
        
    Returns:
        str: Encoded JWT token with user email and longer expiration time
    """
    logger.debug("Creating confirmation token", extra={"email": email})
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=confirm_token_expire_minutes()
    )
    jwt_data = {"sub": email, "exp": expire, "type": "confirmation"}
    encoded_jwt = jwt.encode(jwt_data, key=SECRET_KEY, algorithm=ALGORITHM)
    logger.debug("Confirmation token created")
    return encoded_jwt


def get_subject_for_token_type(
        token: str, token_type: Literal["access", "confirmation"]
) -> str:
    """
    Validate a JWT token and extract the subject if token type matches.
    
    Args:
        token: JWT token to validate and decode
        token_type: Expected token type ('access' or 'confirmation')
        
    Returns:
        str: Email address extracted from the token
        
    Raises:
        HTTPException: If token is invalid, expired, or wrong type
    """
    logger.debug("Getting subject for token type", extra={"type": token_type})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except ExpiredSignatureError as e:
        raise create_credentials_exception("Token has expired") from e
    except JWTError as e:
        raise create_credentials_exception("Invalid token") from e

    email: str = payload.get("sub")

    if email is None:
        raise create_credentials_exception("Token is missing 'sub' field")

    actual_token_type = payload.get("type")
    if actual_token_type is None or actual_token_type != token_type:
        raise create_credentials_exception("Token type is invalid")

    return email


def get_password_hash(password: str) -> str:
    """
    Generate a secure hash of the provided password.
    
    Args:
        password: Plain text password to hash
        
    Returns:
        str: Securely hashed password
    """
    logger.debug("Hashing password")
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify that a plain password matches a hashed password.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Previously hashed password to check against
        
    Returns:
        bool: True if passwords match, False otherwise
    """
    logger.debug("Verifying password")
    return pwd_context.verify(plain_password, hashed_password)


async def get_user(email: str):
    """
    Retrieve a user from the database by email.
    
    Args:
        email: Email address of the user to find
        
    Returns:
        dict: User record if found, None otherwise
    """
    logger.debug("Fetching user from the database", extra={"email": email})
    query = user_table.select().where(user_table.c.email == email)
    user = await database.fetch_one(query)
    if user:
        logger.debug("User found", extra={"email": email})
        return user

    logger.debug("User not found", extra={"email": email})
    return None


async def authenticate_user(email: str, password: str):
    """
    Authenticate a user with email and password.
    
    Args:
        email: User's email address
        password: User's plain text password
        
    Returns:
        dict: User record if authentication succeeds
        
    Raises:
        HTTPException: If authentication fails for any reason
    """
    logger.debug("Authenticating user", extra={"email": email})
    user = await get_user(email)
    if not user:
        raise create_credentials_exception("Incorrect email or password")
    if not verify_password(password, user.password):
        raise create_credentials_exception("Incorrect email or password")
    if not user.confirmed:
        raise create_credentials_exception("User has not confirmed email")
    logger.debug("User authenticated successfully", extra={"email": email})
    return user


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    """
    Get the current authenticated user from a JWT token.
    
    Args:
        token: JWT access token from request
        
    Returns:
        dict: User record of the authenticated user
        
    Raises:
        HTTPException: If token is invalid or user doesn't exist
    """
    logger.debug("Getting current user from token")

    email = get_subject_for_token_type(token, "access")

    user = await get_user(email=email)
    if user is None:
        raise create_credentials_exception("User not found")
    return user
