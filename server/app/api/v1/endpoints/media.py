"""
Media serving API endpoints
"""

import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

from ....core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Base directory for media files
MEDIA_DIR = "temp_media"


@router.get("/{filename}")
async def get_media_file(filename: str):
    """
    Serve a media file from the temp_media directory
    
    Args:
        filename: Name of the file to serve
        
    Returns:
        FileResponse with the requested file
    """
    try:
        # Security: Prevent directory traversal attacks
        # Only allow alphanumeric, dots, dashes, underscores
        if not all(c.isalnum() or c in '._- ' for c in filename):
            logger.warning(f"Invalid filename requested: {filename}")
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        # Construct full path
        file_path = os.path.join(MEDIA_DIR, filename)
        
        # Check if file exists
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            raise HTTPException(status_code=404, detail="File not found")
        
        # Check if path is actually within MEDIA_DIR (additional security)
        real_media_dir = os.path.realpath(MEDIA_DIR)
        real_file_path = os.path.realpath(file_path)
        
        if not real_file_path.startswith(real_media_dir):
            logger.warning(f"Path traversal attempt detected: {filename}")
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Determine media type from extension
        extension = Path(filename).suffix.lower()
        media_type_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        }
        
        media_type = media_type_map.get(extension, 'application/octet-stream')
        
        logger.info(f"Serving media file: {filename} ({media_type})")
        
        return FileResponse(
            path=file_path,
            media_type=media_type,
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving media file {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
