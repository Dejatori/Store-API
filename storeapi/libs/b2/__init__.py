"""
Backblaze B2 Cloud Storage integration module.
Provides utilities for authenticating, connecting to buckets, and uploading files
to the B2 cloud storage service.
"""
import logging
from functools import lru_cache

import b2sdk.v2 as b2

from storeapi.config import config

logger = logging.getLogger(__name__)


@lru_cache()
def b2_api():
    """
    Create and authorize a B2 API client.
    
    Returns:
        B2Api: An authenticated B2 API client instance.
    """
    logger.debug("Creating and authorizing B2 API")
    info = b2.InMemoryAccountInfo()
    b2_client = b2.B2Api(info)

    b2_client.authorize_account("production", config.B2_KEY_ID, config.B2_APPLICATION_KEY)
    return b2_client


@lru_cache()
def b2_get_bucket(api: b2.B2Api):
    """
    Get a B2 bucket by name from the configuration.
    
    Args:
        api: B2 API client instance
        
    Returns:
        Bucket: B2 bucket object
    """
    return api.get_bucket_by_name(config.B2_BUCKET_NAME)


def b2_upload_file(local_file: str, file_name: str) -> str:
    """
    Upload a local file to B2 cloud storage.
    
    Args:
        local_file: Path to the local file to upload
        file_name: Name to assign to the file in B2
        
    Returns:
        str: Download URL for the uploaded file
    """
    api = b2_api()
    logger.debug("Uploading file %s to B2 as %s", local_file, file_name)

    uploaded_file = b2_get_bucket(api).upload_local_file(
        local_file=local_file,
        file_name=file_name,
    )
    download_url = api.get_download_url_for_fileid(uploaded_file.id_)
    logger.debug(
        "Uploaded %s to B2 successfully and got download URL: %s",
        local_file,
        download_url
    )

    return download_url
