"""
Post router test module.
Tests CRUD operations for posts, comments, and likes in the Store API.
Verifies post creation, listing, sorting, commenting, and liking functionality.
"""
import pytest
from httpx import AsyncClient

from storeapi import security


async def create_post(
    body: str, async_client_fixture: AsyncClient, logged_in_token_fixture: str
) -> dict:
    """
    Helper function to create a post.

    Args:
        body: Text content of the post
        async_client_fixture: HTTP client for making requests
        logged_in_token_fixture: Authentication token

    Returns:
        dict: Created post data
    """
    response = await async_client_fixture.post(
        "/post",
        json={"body": body},
        headers={"Authorization": f"Bearer {logged_in_token_fixture}"},
    )
    return response.json()


async def create_comment(
    body: str,
    post_id: int,
    async_client_fixture: AsyncClient,
    logged_in_token_fixture: str,
) -> dict:
    """
    Helper function to create a comment on a post.

    Args:
        body: Text content of the comment
        post_id: ID of the post to comment on
        async_client_fixture: HTTP client for making requests
        logged_in_token_fixture: Authentication token

    Returns:
        dict: Created comment data
    """
    response = await async_client_fixture.post(
        "/comment",
        json={"body": body, "post_id": post_id},
        headers={"Authorization": f"Bearer {logged_in_token_fixture}"},
    )
    return response.json()


async def like_post(
    post_id: int, async_client_fixture: AsyncClient, logged_in_token_fixture: str
) -> dict:
    """
    Helper function to like a post.

    Args:
        post_id: ID of the post to like
        async_client_fixture: HTTP client for making requests
        logged_in_token_fixture: Authentication token

    Returns:
        dict: Like data
    """
    response = await async_client_fixture.post(
        "/like",
        json={"post_id": post_id},
        headers={"Authorization": f"Bearer {logged_in_token_fixture}"},
    )
    return response.json()


@pytest.fixture()
async def created_post_fixture(
    async_client_fixture: AsyncClient, logged_in_token_fixture: str
):
    """
    Fixture that creates a test post.

    Args:
        async_client_fixture: HTTP client for making requests
        logged_in_token_fixture: Authentication token

    Returns:
        dict: Created post data
    """
    return await create_post("Test Post", async_client_fixture, logged_in_token_fixture)


@pytest.fixture()
async def created_comment_fixture(
    async_client_fixture: AsyncClient,
    created_post_fixture: dict,
    logged_in_token_fixture: str,
):
    """
    Fixture that creates a test comment on a post.

    Args:
        async_client_fixture: HTTP client for making requests
        created_post_fixture: Post to comment on
        logged_in_token_fixture: Authentication token

    Returns:
        dict: Created comment data
    """
    return await create_comment(
        "Test Comment", created_post_fixture["id"], async_client_fixture, logged_in_token_fixture
    )


@pytest.mark.anyio
async def test_create_post(
    async_client_fixture: AsyncClient,
    confirmed_user_fixture: dict,
    logged_in_token_fixture: str,
):
    """
    Test creating a new post.

    Verifies that a post can be created and the response contains expected fields.
    """
    body = "Test Post"

    response = await async_client_fixture.post(
        "/post",
        json={"body": body},
        headers={"Authorization": f"Bearer {logged_in_token_fixture}"},
    )

    assert response.status_code == 201
    assert {
               "id": 1,
               "body": body,
               "user_id": confirmed_user_fixture["id"],
               "image_url": None,
           }.items() <= response.json().items()


@pytest.mark.anyio
async def test_create_post_with_prompt(
        async_client_fixture: AsyncClient,
        logged_in_token_fixture: str,
        mocker,
):
    """
    Test creating a post with an image generation prompt.

    Verifies that the image generation task is called with the correct parameters.
    """
    body = "Test Post"
    prompt = "A cat"

    # Mock generate_image_and_add_to_post.delay to verify its call
    mock_task = mocker.patch("storeapi.tasks.generate_image_and_add_to_post.delay")

    response = await async_client_fixture.post(
        "/post",
        json={"body": body},
        params={"prompt": prompt},
        headers={"Authorization": f"Bearer {logged_in_token_fixture}"},
    )

    assert response.status_code == 201
    assert {
               "id": 1,
               "body": body,
               "image_url": None,
           }.items() <= response.json().items()

    mock_task.assert_called_once()
    call_args = mock_task.call_args[0]
    assert prompt in call_args


@pytest.mark.anyio
async def test_create_post_expired_token(
        async_client_fixture: AsyncClient, confirmed_user_fixture: dict, mocker
):
    """
    Test creating a post with an expired token.

    Verifies that the request is rejected with a 401 Unauthorized response.
    """
    mocker.patch("storeapi.security.access_token_expire_minutes", return_value=-1)
    token = security.create_access_token(confirmed_user_fixture["email"])
    response = await async_client_fixture.post(
        "/post",
        json={"body": "Test Post"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert "Token has expired" in response.json()["detail"]


@pytest.mark.anyio
async def test_create_post_missing_data(
        async_client_fixture: AsyncClient, logged_in_token_fixture: str
):
    """
    Test creating a post with missing required data.

    Verifies that the request is rejected with a 422 Unprocessable Entity response.
    """
    response = await async_client_fixture.post(
        "/post", json={}, headers={"Authorization": f"Bearer {logged_in_token_fixture}"}
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_like_post(
    async_client_fixture: AsyncClient,
    created_post_fixture: dict,
    logged_in_token_fixture: str,
):
    """
    Test liking a post.

    Verifies that a like can be created and the response contains expected fields.
    """
    response = await async_client_fixture.post(
        "/like",
        json={"post_id": created_post_fixture["id"]},
        headers={"Authorization": f"Bearer {logged_in_token_fixture}"},
    )

    assert response.status_code == 201
    assert {
               "post_id": created_post_fixture["id"],
               "user_id": created_post_fixture["user_id"],
           }.items() <= response.json().items()


@pytest.mark.anyio
async def test_get_all_posts(async_client_fixture: AsyncClient, created_post_fixture: dict):
    """
    Test retrieving all posts.

    Verifies that all posts can be retrieved and the response includes like counts.
    """
    response = await async_client_fixture.get("/post")

    assert response.status_code == 200
    assert response.json() == [{**created_post_fixture, "likes": 0}]


@pytest.mark.anyio
@pytest.mark.parametrize(
    "sorting, expected_order",
    [("new", [2, 1]), ("old", [1, 2])],
)
async def test_get_all_posts_sorting(
        async_client_fixture: AsyncClient,
        logged_in_token_fixture: str,
        sorting: str,
        expected_order: list[int],
):
    """
    Test sorting posts by creation time.

    Args:
        sorting: Sort direction ('new' or 'old')
        expected_order: Expected order of post IDs after sorting

    Verifies that posts are sorted as expected based on the sorting parameter.
    """
    await create_post("Test Post 1", async_client_fixture, logged_in_token_fixture)
    await create_post("Test Post 2", async_client_fixture, logged_in_token_fixture)

    response = await async_client_fixture.get("/post", params={"sorting": sorting})

    assert response.status_code == 200

    data = response.json()
    post_id = [post["id"] for post in data]

    assert post_id == expected_order


@pytest.mark.anyio
async def test_get_all_posts_sort_likes(
        async_client_fixture: AsyncClient,
        logged_in_token_fixture: str,
):
    """
    Test sorting posts by like count.

    Verifies that posts are sorted by most likes when the 'most_likes' sorting is specified.
    """
    await create_post("Test Post 1", async_client_fixture, logged_in_token_fixture)
    await create_post("Test Post 2", async_client_fixture, logged_in_token_fixture)
    await like_post(1, async_client_fixture, logged_in_token_fixture)

    response = await async_client_fixture.get("/post", params={"sorting": "most_likes"})

    assert response.status_code == 200

    data = response.json()
    post_id = [post["id"] for post in data]
    expected_order = [1, 2]

    assert post_id == expected_order


@pytest.mark.anyio
async def test_get_all_posts_wrong_sorting(
        async_client_fixture: AsyncClient,
):
    """
    Test using an invalid sorting parameter.

    Verifies that the request is rejected with a 422 Unprocessable Entity response.
    """
    response = await async_client_fixture.get("/post", params={"sorting": "wrong"})

    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_comment(
        async_client_fixture: AsyncClient,
        created_post_fixture: dict,
        confirmed_user_fixture: dict,
        logged_in_token_fixture: str,
):
    """
    Test creating a comment on a post.

    Verifies that a comment can be created and the response contains expected fields.
    """
    body = "Test Comment"

    response = await async_client_fixture.post(
        "/comment",
        json={"body": body, "post_id": created_post_fixture["id"]},
        headers={"Authorization": f"Bearer {logged_in_token_fixture}"},
    )
    assert response.status_code == 201
    assert {
               "id": 1,
               "body": body,
               "post_id": created_post_fixture["id"],
               "user_id": confirmed_user_fixture["id"],
           }.items() <= response.json().items()


@pytest.mark.anyio
async def test_get_comments_on_post(
    async_client_fixture: AsyncClient,
    created_post_fixture: dict,
    created_comment_fixture: dict,
):
    """
    Test retrieving comments for a specific post.

    Verifies that all comments for a post can be retrieved.
    """
    response = await async_client_fixture.get(f"/post/{created_post_fixture['id']}/comment")

    assert response.status_code == 200
    assert response.json() == [created_comment_fixture]


@pytest.mark.anyio
async def test_get_comments_on_post_empty(
        async_client_fixture: AsyncClient, created_post_fixture: dict
):
    """
    Test retrieving comments for a post that has no comments.

    Verifies that an empty list is returned when a post has no comments.
    """
    response = await async_client_fixture.get(f"/post/{created_post_fixture['id']}/comment")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.anyio
async def test_get_post_with_comments(
    async_client_fixture: AsyncClient,
    created_post_fixture: dict,
    created_comment_fixture: dict,
):
    """
    Test retrieving a post with its comments.

    Verifies that a post can be retrieved with its comments and like count.
    """
    response = await async_client_fixture.get(f"/post/{created_post_fixture['id']}")

    assert response.status_code == 200
    assert response.json() == {
        "post": {**created_post_fixture, "likes": 0},
        "comments": [created_comment_fixture],
    }


@pytest.mark.anyio
async def test_get_missing_post_with_comments(
        async_client_fixture: AsyncClient
):
    """
    Test retrieving a non-existent post.

    Verifies that a 404 Not Found response is returned when a post doesn't exist.
    """
    response = await async_client_fixture.get("/post/2")
    assert response.status_code == 404
