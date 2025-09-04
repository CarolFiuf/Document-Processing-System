from fastapi import APIRouter
from app.models.database import engine
import time
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "timestamp": time.time()
    }

@router.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check including database"""
    
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "checks": {}
    }
    
    # Database check
    try:
        with engine.connect() as connection:
            from sqlalchemy import text
            connection.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["checks"]["database"] = "unhealthy"
        health_status["status"] = "unhealthy"
    
    # File system check
    try:
        import os
        from app.config import settings
        
        if os.path.exists(settings.upload_path) and os.access(settings.upload_path, os.W_OK):
            health_status["checks"]["file_system"] = "healthy"
        else:
            health_status["checks"]["file_system"] = "unhealthy"
            health_status["status"] = "unhealthy"
    except Exception as e:
        logger.error(f"File system health check failed: {e}")
        health_status["checks"]["file_system"] = "unhealthy"
        health_status["status"] = "unhealthy"
    
    return health_status