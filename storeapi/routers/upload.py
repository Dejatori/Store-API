"""
Upload router module for the Store API application.
Handles file uploads from clients, processes files in chunks,
and uploads them to Backblaze B2 cloud storage.
"""
import logging
import tempfile

import aiofiles
from fastapi import APIRouter, HTTPException, UploadFile, status

from storeapi.libs.b2 import b2_upload_file

logger = logging.getLogger(__name__)

router = APIRouter()

# Client split up file into chunks of 1MB
# Client sends up chunks 1 at a time
# Client sends the last chunk and then fastapi will put the file together in a temp file
CHUNK_SIZE = 1024 * 1024


@router.post("/upload", status_code=201)
async def upload_file(file: UploadFile):
    """
    Process an uploaded file in chunks and store it in B2 cloud storage.
    
    Args:
        file: The uploaded file from the client
        
    Returns:
        A dictionary with upload confirmation and file URL
        
    Raises:
        HTTPException: If there's an error during the file upload process
    """
    try:
        with tempfile.NamedTemporaryFile() as temp_file:
            filename = temp_file.name
            logger.info("Saving uploaded file temporarily to %s", filename)
            async with aiofiles.open(filename, "wb") as f:  # Binary write
                while chunck := await file.read(CHUNK_SIZE):
                    await f.write(chunck)

            file_url = b2_upload_file(local_file=filename, file_name=file.filename)
    except Exception as exc:
        logger.exception("Error uploading file")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="There was an error uploading the file",
        ) from exc

    return {"detail": f"Successfully uploaded {file.filename}", "file_url": file_url}
