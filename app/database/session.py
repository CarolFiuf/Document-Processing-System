# app/database/session.py - COMPLETE VERSION
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
from app.models.database import SessionLocal, engine
import logging

logger = logging.getLogger(__name__)

def get_db() -> Session:
    """FastAPI dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    except Exception as e:
        logger.error(f"Unexpected database error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

@contextmanager
def get_db_session():
    """Context manager for database sessions"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except SQLAlchemyError as e:
        logger.error(f"Database transaction error: {e}")
        db.rollback()
        raise
    except Exception as e:
        logger.error(f"Unexpected error in database transaction: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def check_database_connection() -> bool:
    """Check if database connection is working"""
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False

async def get_database_stats() -> dict:
    """Get database statistics"""
    try:
        db = SessionLocal()
        
        # Get table row counts
        from app.models.database import Document
        
        total_docs = db.query(Document).count()
        completed_docs = db.query(Document).filter(Document.status == 'completed').count()
        failed_docs = db.query(Document).filter(Document.status == 'failed').count()
        processing_docs = db.query(Document).filter(Document.status == 'processing').count()
        
        # Get average processing time
        avg_processing_time = db.query(
            db.func.avg(Document.processing_time_seconds)
        ).filter(
            Document.processing_time_seconds.isnot(None)
        ).scalar() or 0.0
        
        db.close()
        
        return {
            "total_documents": total_docs,
            "completed_documents": completed_docs,
            "failed_documents": failed_docs,
            "processing_documents": processing_docs,
            "average_processing_time": round(avg_processing_time, 2),
            "success_rate": round((completed_docs / total_docs * 100) if total_docs > 0 else 0, 2)
        }
        
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        return {
            "error": str(e),
            "total_documents": 0,
            "completed_documents": 0,
            "failed_documents": 0,
            "processing_documents": 0,
            "average_processing_time": 0.0,
            "success_rate": 0.0
        }