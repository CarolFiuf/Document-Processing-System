from sqlalchemy import create_engine, Column, String, DateTime, Text, Float, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from app.config import settings

# Create engine
if settings.database_url.startswith("sqlite"):
    engine = create_engine(
        settings.database_url, 
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(settings.database_url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"
    
    # Primary fields
    id = Column(String, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    document_type = Column(String, nullable=True)
    
    # Status tracking
    status = Column(String, default="uploaded")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Processing results
    extracted_text = Column(Text, nullable=True)
    ocr_confidence = Column(Float, nullable=True)
    processing_time_seconds = Column(Float, nullable=True)
    llm_analysis = Column(Text, nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Metadata
    pages_count = Column(Integer, nullable=True)
    language_detected = Column(String, nullable=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.original_filename,
            "file_size_bytes": self.file_size_bytes,
            "document_type": self.document_type,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at is not None else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at is not None else None,
            "processing_time_seconds": self.processing_time_seconds,
            "ocr_confidence": self.ocr_confidence,
            "pages_count": self.pages_count,
            "language_detected": self.language_detected,
            "error_message": self.error_message
        }

# Create tables
Base.metadata.create_all(bind=engine)