from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class DocumentType(str, Enum):
    CONTRACT = "contract"
    INVOICE = "invoice"
    REPORT = "report"
    LETTER = "letter"
    OTHER = "other"

class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    status: DocumentStatus
    file_size_bytes: int
    message: str

class DocumentStatusResponse(BaseModel):
    id: str
    filename: str
    file_size_bytes: int
    document_type: Optional[str]
    status: DocumentStatus
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    processing_time_seconds: Optional[float]
    ocr_confidence: Optional[float]
    pages_count: Optional[int]
    language_detected: Optional[str]
    error_message: Optional[str]

class DocumentMetadata(BaseModel):
    ocr_confidence: Optional[float]
    processing_time_seconds: Optional[float]
    pages_count: Optional[int]
    language_detected: Optional[str]
    file_size_bytes: int

class DocumentResults(BaseModel):
    document_id: str
    status: DocumentStatus
    extracted_text: Optional[str]
    llm_analysis: Optional[dict]
    metadata: DocumentMetadata

class DocumentListResponse(BaseModel):
    documents: List[DocumentStatusResponse]
    total: int
    skip: int
    limit: int