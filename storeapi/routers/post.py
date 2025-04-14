"""
Post router module for the Store API application.
Handles all HTTP requests related to posts, comments, and likes.
Provides endpoints for creating, retrieving, and interacting with user posts.
"""
import logging
from enum import Enum
from typing import Annotated

import sqlalchemy
from fastapi import APIRouter, Depends, HTTPException, Request

from storeapi.config import config
from storeapi.database import comment_table, database, like_table, post_table
from storeapi.models.post import (
    Comment,
    CommentIn,
    PostLike,
    PostLikeIn,
    UserPost,
    UserPostIn,
    UserPostWithComments,
    UserPostWithLikes,
)
from storeapi.models.user import User
from storeapi.security import get_current_user
from storeapi.tasks import generate_image_and_add_to_post

router = APIRouter()

logger = logging.getLogger(__name__)

select_post_and_likes = (
    sqlalchemy.select(post_table, sqlalchemy.func.count(like_table.c.id).label("likes")) # pylint: disable=not-callable
    .select_from(post_table.outerjoin(like_table))
    .group_by(post_table.c.id)
)


async def find_post(post_id: int):
    """
    Find a post by its ID in the database.
    
    Args:
        post_id: The ID of the post to find
        
    Returns:
        The post record if found, None otherwise
    """
    logger.info("Finding post with id %s", post_id)

    query = post_table.select().where(post_table.c.id == post_id)

    logger.debug(query)

    return await database.fetch_one(query)


@router.post("/post", response_model=UserPost, status_code=201)
async def create_post(
        post: UserPostIn,
        current_user: Annotated[User, Depends(get_current_user)],
        request: Request,
        prompt: str = None,
):
    """
    Create a new post with optional image generation.
    
    Args:
        post: The post content to create
        current_user: The authenticated user making the request
        request: The FastAPI request object
        prompt: Optional text prompt for image generation
        
    Returns:
        The created post data including the new ID
    """
    logger.info("Creating post")

    data = {**post.model_dump(), "user_id": current_user.id}
    query = post_table.insert().values(data)

    logger.debug(query)

    last_record_id = await database.execute(query)

    if prompt:
        logger.info(
            "Launching image generation for post %s with prompt: %s...",
            last_record_id,
            prompt[:30]
        )
        post_url = str(
            request.url_for("get_post_with_comments", post_id=last_record_id)
        )

        generate_image_and_add_to_post.delay(
            current_user.email,
            str(last_record_id),
            post_url,
            config.DATABASE_URL,
            prompt,
        )

    return {**data, "id": last_record_id}


class PostSorting(str, Enum):
    """
    Enumeration for post sorting options.
    Defines the available sorting mechanisms for post listings.
    """
    NEW = "new"  # http://api.com/post?sorting=new
    OLD = "old"  # http://api.com/post?sorting=old
    MOST_LIKES = "most_likes"  # http://api.com/post?sorting=most_likes


@router.get("/post", response_model=list[UserPostWithLikes], status_code=200)
async def get_all_posts(sorting: PostSorting = PostSorting.NEW):
    """
    Get all posts with optional sorting.
    
    Args:
        sorting: The sorting method to use (new, old, or most_likes)
        
    Returns:
        List of posts with like counts, sorted according to the specified criteria
    """
    logger.info("Getting all posts")

    query = None
    if sorting == PostSorting.NEW:
        query = select_post_and_likes.order_by(post_table.c.id.desc())
    elif sorting == PostSorting.OLD:
        query = select_post_and_likes.order_by(post_table.c.id.asc())
    elif sorting == PostSorting.MOST_LIKES:
        query = select_post_and_likes.order_by(sqlalchemy.desc("likes"))

    logger.debug(query)

    return await database.fetch_all(query)


@router.post("/comment", response_model=Comment, status_code=201)
async def create_comment(
        comment: CommentIn, current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Create a new comment on a post.
    
    Args:
        comment: The comment content and post ID
        current_user: The authenticated user making the comment
        
    Returns:
        The created comment data including the new ID
        
    Raises:
        HTTPException: If the post doesn't exist
    """
    logger.info("Creating comment")

    post = await find_post(comment.post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Missing post")

    data = {**comment.model_dump(), "user_id": current_user.id}
    query = comment_table.insert().values(data)

    logger.debug(query)

    last_record_id = await database.execute(query)
    return {**data, "id": last_record_id}


@router.get("/post/{post_id}/comment", response_model=list[Comment])
async def get_comments_on_post(post_id: int):
    """
    Get all comments for a specific post.
    
    Args:
        post_id: The ID of the post to retrieve comments for
        
    Returns:
        List of comments on the specified post
    """
    logger.info("Getting comments on post")

    query = comment_table.select().where(comment_table.c.post_id == post_id)

    logger.debug(query)

    return await database.fetch_all(query)


@router.get("/post/{post_id}", response_model=UserPostWithComments)
async def get_post_with_comments(post_id: int):
    """
    Get a post and all its comments.
    
    Args:
        post_id: The ID of the post to retrieve
        
    Returns:
        The post with its like count and all comments
        
    Raises:
        HTTPException: If the post doesn't exist
    """
    logger.info("Getting post and its comments")

    query = select_post_and_likes.where(post_table.c.id == post_id)

    logger.debug(query)

    post = await database.fetch_one(query)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    return {
        "post": post,
        "comments": await get_comments_on_post(post_id),
    }


@router.post("/like", response_model=PostLike, status_code=201)
async def like_post(
        post_like: PostLikeIn, current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Like a post.
    
    Args:
        post_like: The post ID to like
        current_user: The authenticated user performing the like action
        
    Returns:
        The created like data including the new ID
        
    Raises:
        HTTPException: If the post doesn't exist
    """
    logger.info("Liking post")

    post = await find_post(post_like.post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    data = {**post_like.model_dump(), "user_id": current_user.id}
    query = like_table.insert().values(data)

    logger.debug(query)

    last_record_id = await database.execute(query)
    return {**data, "id": last_record_id}
