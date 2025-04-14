"""
User model definitions for the Store API application.
Contains Pydantic models that define the structure of user data
for both requests and responses.
"""
from pydantic import BaseModel


class User(BaseModel):
    """
    User response model representing a user in the system.
    Contains the user's ID and email address, but omits sensitive information
    like passwords for security.
    """
    id: int
    email: str


class UserIn(BaseModel):
    """
    User input model for user registration and authentication.
    Contains the user's email address and password which are required
    for creating a new user account or authenticating an existing user.
    """
    email: str
    password: str
