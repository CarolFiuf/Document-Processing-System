from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
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
    RESUME = "resume"
    REPORT = "report"
    LETTER = "letter"
    OTHER = "other"

class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    status: DocumentStatus
    file_size_bytes: int
    document_type: Optional[str] = None
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
    llm_analysis: Optional[Dict[str, Any]]
    metadata: DocumentMetadata

class SimilarDocument(BaseModel):
    document_id: str
    similarity_score: float
    text_preview: str
    metadata: Dict[str, Any]
    filename: Optional[str] = None

class SimilarDocumentsResponse(BaseModel):
    document_id: str
    similar_documents: List[SimilarDocument]
    total_found: int

class DocumentInsights(BaseModel):
    document_info: Dict[str, Any]
    processing_results: Dict[str, Any]
    llm_analysis: Dict[str, Any]
    similar_documents: List[SimilarDocument]
    recommendations: List[str]

class DocumentListResponse(BaseModel):
    documents: List[DocumentStatusResponse]
    total: int
    skip: int
    limit: int
    filters: Optional[Dict[str, Any]] = None

# Analytics schemas
class ProcessingStats(BaseModel):
    total_documents: int
    completed_documents: int
    failed_documents: int
    average_processing_time: float
    total_processing_time: float
    documents_by_type: Dict[str, int]
    documents_by_language: Dict[str, int]

class SystemHealth(BaseModel):
    api_status: str
    database_status: str
    redis_status: str
    milvus_status: str
    vllm_status: str
    total_documents: int
    processing_queue_size: int