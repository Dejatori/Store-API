"""
Upload router test module.
Tests file upload functionality including image uploads, temporary file handling,
and integration with external storage services.
"""
import contextlib
import os
import pathlib
import tempfile

import pytest
from httpx import AsyncClient

# pylint: disable=redefined-outer-name


@pytest.fixture()
def sample_image(fs) -> pathlib.Path:
    """
    Create a sample image file for testing.
    
    Args:
        fs: PyFakeFS fixture for file system operations
        
    Returns:
        pathlib.Path: Path to the created sample image
    """
    path = (pathlib.Path(__file__).parent / "assets" / "myfile.png").resolve()
    fs.create_file(path)
    return path


@pytest.fixture(autouse=True)
def mock_b2_upload_file(mocker):
    """
    Mock the B2 file upload functionality.
    
    Args:
        mocker: pytest-mock fixture
        
    Returns:
        MagicMock: The mocked upload function
    """
    return mocker.patch(
        "storeapi.routers.upload.b2_upload_file",
        return_value="https://fakeurl.com",
    )


@pytest.fixture(autouse=True)
def aiofiles_mock_open(mocker, fs): # pylint: disable=unused-argument
    """
    Mock aiofiles.open to use the pyfakefs filesystem.
    
    Args:
        mocker: pytest-mock fixture
        fs: PyFakeFS fixture for file system operations
        
    Returns:
        MagicMock: The mocked open function
    """
    # Mock aiofiles.open to use the pyfakefs filesystem
    mock_open = mocker.patch("aiofiles.open")

    @contextlib.asynccontextmanager
    async def async_file_open(fname: str, mode: str = "r"):
        out_fs_mock = mocker.AsyncMock(name=f"async_file_open:{fname!r}/{mode!r}")
        # Use binary mode when needed to avoid encoding warning
        with open(fname, mode, encoding=None if 'b' in mode else 'utf-8') as fin:
            out_fs_mock.read.side_effect = fin.read
            out_fs_mock.write.side_effect = fin.write
            yield out_fs_mock

    mock_open.side_effect = async_file_open
    return mock_open


async def call_upload_endpoint(
        async_client_fixture: AsyncClient, token: str, sample_image: pathlib.Path
):
    """
    Helper function to call the upload endpoint.
    
    Args:
        async_client_fixture: HTTP client for making requests
        token: Authentication token
        sample_image: Path to the image file to upload
        
    Returns:
        Response: The HTTP response from the upload endpoint
    """
    return await async_client_fixture.post(
        "/upload",
        files={"file": open(sample_image, "rb")},
        headers={"Authorization": f"Bearer {token}"},
    )


@pytest.mark.anyio
async def test_upload_image(
        async_client_fixture: AsyncClient, logged_in_token_fixture: str, sample_image: pathlib.Path
):
    """
    Test uploading an image file.
    
    Verifies that the image is uploaded successfully and the correct response is returned.
    """
    response = await call_upload_endpoint(
        async_client_fixture, logged_in_token_fixture, sample_image
    )
    assert response.status_code == 201
    assert response.json() == {
        "detail": f"Successfully uploaded {sample_image.name}",
        "file_url": "https://fakeurl.com",
    }


@pytest.mark.anyio
async def test_temp_file_remove_after_upload(
        async_client_fixture: AsyncClient,
        logged_in_token_fixture: str,
        sample_image: pathlib.Path,
        mocker
):
    """
    Test that temporary files are removed after upload.
    
    Verifies that the temporary file created during upload is properly cleaned up.
    """
    named_temp_file_spy = mocker.spy(tempfile, "NamedTemporaryFile")

    response = await call_upload_endpoint(
        async_client_fixture, logged_in_token_fixture, sample_image
    )
    assert response.status_code == 201

    created_temp_file = named_temp_file_spy.spy_return

    assert not os.path.exists(created_temp_file.name)
