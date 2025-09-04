# app/models/database.py - COMPLETE POSTGRESQL VERSION
from sqlalchemy import create_engine, Column, String, DateTime, Text, Float, Integer, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime, timezone
import uuid
import os
from app.config import settings

# Database engine with connection pooling
if settings.database_url.startswith("sqlite"):
    # SQLite for local development
    engine = create_engine(
        settings.database_url, 
        connect_args={"check_same_thread": False},
        pool_pre_ping=True
    )
else:
    # PostgreSQL for production
    engine = create_engine(
        settings.database_url,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=False  # Set to True for SQL debugging
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"
    
    # Primary fields with UUID for PostgreSQL
    id = Column(
        String(36) if settings.database_url.startswith("sqlite") else UUID(as_uuid=False), 
        primary_key=True, 
        index=True,
        default=lambda: str(uuid.uuid4())
    )
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    document_type = Column(String(100), nullable=True)
    
    # Status tracking with constraints
    status = Column(
        String(50), 
        nullable=False, 
        default="uploaded",
        index=True
    )
    created_at = Column(
        DateTime(timezone=True), 
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True
    )
    updated_at = Column(
        DateTime(timezone=True), 
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    
    # Processing results
    extracted_text = Column(Text, nullable=True)
    ocr_confidence = Column(Float, nullable=True)
    processing_time_seconds = Column(Float, nullable=True)
    
    # LLM analysis stored as JSON
    llm_analysis = Column(
        JSONB if not settings.database_url.startswith("sqlite") else Text,
        nullable=True
    )
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    
    # Metadata
    pages_count = Column(Integer, nullable=True)
    language_detected = Column(String(50), nullable=True, index=True)
    
    # Vector processing status
    vector_processed = Column(Boolean, nullable=False, default=False)
    embedding_created_at = Column(DateTime(timezone=True), nullable=True)
    
    # Additional indexes for performance
    __table_args__ = (
        Index('idx_documents_status_created', 'status', 'created_at'),
        Index('idx_documents_type_language', 'document_type', 'language_detected'),
        Index('idx_documents_processing_time', 'processing_time_seconds'),
        Index('idx_documents_vector_status', 'vector_processed', 'status'),
    )
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "filename": self.original_filename,
            "file_size_bytes": self.file_size_bytes,
            "document_type": self.document_type,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "processing_time_seconds": self.processing_time_seconds,
            "ocr_confidence": self.ocr_confidence,
            "pages_count": self.pages_count,
            "language_detected": self.language_detected,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "vector_processed": self.vector_processed
        }
    
    def get_llm_analysis(self):
        """Get parsed LLM analysis"""
        if not self.llm_analysis:
            return None
        
        if isinstance(self.llm_analysis, dict):
            return self.llm_analysis
        
        try:
            import json
            return json.loads(self.llm_analysis)
        except (json.JSONDecodeError, TypeError):
            return {"raw": str(self.llm_analysis)}
    
    def set_llm_analysis(self, analysis_data):
        """Set LLM analysis with proper JSON handling"""
        if isinstance(analysis_data, dict):
            if not settings.database_url.startswith("sqlite"):
                # PostgreSQL JSONB
                self.llm_analysis = analysis_data
            else:
                # SQLite Text
                import json
                self.llm_analysis = json.dumps(analysis_data, ensure_ascii=False)
        else:
            self.llm_analysis = str(analysis_data)

# Create tables
Base.metadata.create_all(bind=engine)