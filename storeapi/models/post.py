"""
Post model definitions for the Store API application.
Contains Pydantic models for user posts, comments, and likes
that define the structure of request and response data.
"""
from typing import Optional

from pydantic import BaseModel, ConfigDict


class UserPostIn(BaseModel):
    """
    Input model for creating a new user post.
    Contains only the post content body.
    """
    body: str


class UserPost(UserPostIn):
    """
    Complete user post model that extends the input model.
    Includes server-generated fields like ID, user_id, and optional image URL.
    """
    id: int
    user_id: int
    image_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UserPostWithLikes(UserPost):
    """
    User post model that includes like count information.
    Extends the base UserPost model with a likes field.
    """
    likes: int

    model_config = ConfigDict(from_attributes=True)


class CommentIn(BaseModel):
    """
    Input model for creating a new comment.
    Contains the comment content and associated post ID.
    """
    body: str
    post_id: int


class Comment(CommentIn):
    """
    Complete comment model that extends the input model.
    Includes server-generated fields like ID and user_id.
    """
    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)


class UserPostWithComments(BaseModel):
    """
    Composite model that contains a post with its like count
    and all associated comments.
    """
    post: UserPostWithLikes
    comments: list[Comment]


class PostLikeIn(BaseModel):
    """
    Input model for creating a new post like.
    Contains only the post ID to be liked.
    """
    post_id: int


class PostLike(PostLikeIn):
    """
    Complete post like model that extends the input model.
    Includes server-generated fields like ID and user_id.
    """
    id: int
    user_id: int
