from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List
import logging

from app.database.session import get_db
from app.models.database import Document
from app.models.schemas import (
    DocumentUploadResponse, 
    DocumentStatusResponse, 
    DocumentResults,
    DocumentListResponse,
    DocumentStatus,
    DocumentType
)
from app.services.document_service import DocumentService
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Allowed file extensions
ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.docx', '.doc'}

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    document_type: Optional[DocumentType] = None,
    db: Session = Depends(get_db)
):
    """Upload a document for processing"""
    
    logger.info(f"Uploading document: {file.filename}")
    
    # Validate file type
    file_extension = '.' + file.filename.split('.')[-1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type: {file_extension}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check file size
    if file.size > settings.max_file_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.max_file_size} bytes"
        )
    
    try:
        # Use document service
        document_service = DocumentService()
        result = await document_service.upload_document(
            file=file,
            document_type=document_type.value if document_type else None,
            db=db
        )
        
        # Queue for background processing
        background_tasks.add_task(
            document_service.process_document_background, 
            result["document_id"]
        )
        
        logger.info(f"Document uploaded successfully: {result['document_id']}")
        return result
        
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{doc_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(doc_id: str, db: Session = Depends(get_db)):
    """Get document processing status"""
    
    document = db.query(Document).filter(Document.id == doc_id).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return DocumentStatusResponse(**document.to_dict())

@router.get("/{doc_id}/results", response_model=DocumentResults)
async def get_document_results(doc_id: str, db: Session = Depends(get_db)):
    """Get document processing results"""
    
    document = db.query(Document).filter(Document.id == doc_id).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if document.status != DocumentStatus.COMPLETED.value:
        raise HTTPException(
            status_code=400, 
            detail=f"Document processing not completed. Current status: {document.status}"
        )
    
    # Parse LLM analysis if available
    llm_analysis = None
    if document.llm_analysis:
        try:
            import json
            llm_analysis = json.loads(document.llm_analysis)
        except:
            llm_analysis = {"raw": document.llm_analysis}
    
    return DocumentResults(
        document_id=doc_id,
        status=document.status,
        extracted_text=document.extracted_text,
        llm_analysis=llm_analysis,
        metadata={
            "ocr_confidence": document.ocr_confidence,
            "processing_time_seconds": document.processing_time_seconds,
            "pages_count": document.pages_count,
            "language_detected": document.language_detected,
            "file_size_bytes": document.file_size_bytes
        }
    )

@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    skip: int = 0,
    limit: int = 50,
    status: Optional[DocumentStatus] = None,
    document_type: Optional[DocumentType] = None,
    db: Session = Depends(get_db)
):
    """List documents with optional filtering"""
    
    query = db.query(Document)
    
    if status:
        query = query.filter(Document.status == status.value)
    
    if document_type:
        query = query.filter(Document.document_type == document_type.value)
    
    # Get total count
    total = query.count()
    
    # Get documents with pagination
    documents = query.order_by(Document.created_at.desc()).offset(skip).limit(limit).all()
    
    return DocumentListResponse(
        documents=[DocumentStatusResponse(**doc.to_dict()) for doc in documents],
        total=total,
        skip=skip,
        limit=limit
    )

@router.delete("/{doc_id}")
async def delete_document(doc_id: str, db: Session = Depends(get_db)):
    """Delete a document and its file"""
    
    document_service = DocumentService()
    result = await document_service.delete_document(doc_id, db)
    
    return {"message": "Document deleted successfully"}