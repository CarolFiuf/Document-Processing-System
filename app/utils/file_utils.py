import os
import shutil
import logging
from pathlib import Path
from fastapi import UploadFile

from app.config import settings

logger = logging.getLogger(__name__)

async def save_uploaded_file(file: UploadFile, file_path: str) -> None:
    """Save uploaded file to specified path"""
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        logger.info(f"File saved: {file_path}")
        
    except Exception as e:
        logger.error(f"Error saving file {file_path}: {e}")
        # Cleanup partial file
        if os.path.exists(file_path):
            os.remove(file_path)
        raise e

def cleanup_file(file_path: str) -> None:
    """Safely delete a file"""
    
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"File cleaned up: {file_path}")
    except Exception as e:
        logger.warning(f"Could not cleanup file {file_path}: {e}")

def ensure_directory(path: str) -> None:
    """Ensure directory exists"""
    
    Path(path).mkdir(parents=True, exist_ok=True)

def get_file_size(file_path: str) -> int:
    """Get file size in bytes"""
    
    if os.path.exists(file_path):
        return os.path.getsize(file_path)
    return 0