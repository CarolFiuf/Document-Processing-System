from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks, Query
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
    DocumentInsights,  # New schema
    SimilarDocumentsResponse,  # New schema
    DocumentStatus,
    DocumentType
)
from app.services.document_service import DocumentService
from app.services.cache_service import CacheService
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize services
document_service = DocumentService()
cache_service = CacheService()

ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.docx', '.doc'}

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    document_type: Optional[DocumentType] = None,
    db: Session = Depends(get_db)
):
    """Upload a document for processing with AI analysis"""
    
    logger.info(f"Uploading document: {file.filename}")
    
    # Validate file type
    file_extension = '.' + file.filename.split('.')[-1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type: {file_extension}"
        )
    
    # Check file size
    if file.size and file.size > settings.max_file_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.max_file_size} bytes"
        )
    
    try:
        # Upload document
        result = await document_service.upload_document(
            file=file,
            document_type=document_type.value if document_type else None,
            db=db
        )
        
        # Queue for enhanced background processing (OCR + LLM + Vector)
        background_tasks.add_task(
            document_service.process_document_background, 
            result["document_id"]
        )
        
        logger.info(f"Document uploaded and queued: {result['document_id']}")
        return result
        
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{doc_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(doc_id: str, db: Session = Depends(get_db)):
    """Get document processing status"""
    
    # Try cache first
    cached_status = await cache_service.get_document_status(doc_id)
    if cached_status:
        return cached_status
    
    document = db.query(Document).filter(Document.id == doc_id).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    status_response = DocumentStatusResponse(**document.to_dict())
    
    # Cache status for 30 seconds (for active polling)
    await cache_service.set_document_status(doc_id, status_response.dict())
    
    return status_response

@router.get("/{doc_id}/results", response_model=DocumentResults)
async def get_document_results(doc_id: str, db: Session = Depends(get_db)):
    """Get complete document processing results including LLM analysis"""
    
    # Try cache first
    cached_results = await cache_service.get_document_results(doc_id)
    if cached_results:
        return cached_results
    
    document = db.query(Document).filter(Document.id == doc_id).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if document.status != DocumentStatus.COMPLETED.value:
        raise HTTPException(
            status_code=400, 
            detail=f"Document processing not completed. Status: {document.status}"
        )
    
    # Parse LLM analysis
    llm_analysis = None
    if document.llm_analysis:
        try:
            import json
            llm_analysis = json.loads(document.llm_analysis)
        except:
            llm_analysis = {"raw": document.llm_analysis}
    
    results = DocumentResults(
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
    
    # Cache results for 1 hour
    await cache_service.set_document_results(doc_id, results.dict())
    
    return results

@router.get("/{doc_id}/insights", response_model=DocumentInsights)
async def get_document_insights(doc_id: str, db: Session = Depends(get_db)):
    """Get comprehensive document insights and recommendations"""
    
    try:
        insights = await document_service.get_document_insights(doc_id, db)
        return DocumentInsights(**insights)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting insights for {doc_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get document insights")

@router.get("/{doc_id}/similar", response_model=SimilarDocumentsResponse)
async def get_similar_documents(
    doc_id: str,
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """Find documents similar to the given document"""
    
    try:
        # Get the document
        document = db.query(Document).filter(Document.id == doc_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        if not document.extracted_text:
            raise HTTPException(status_code=400, detail="Document has no extracted text for similarity search")
        
        # Search for similar documents
        similar_docs = await document_service.search_similar_documents(
            query_text=document.extracted_text[:1000],  # First 1000 chars
            limit=limit,
            document_type=document.document_type
        )
        
        return SimilarDocumentsResponse(
            document_id=doc_id,
            similar_documents=similar_docs,
            total_found=len(similar_docs)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding similar documents for {doc_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to find similar documents")

@router.post("/search")
async def search_documents(
    query: str = Query(..., min_length=3),
    document_type: Optional[DocumentType] = None,
    limit: int = Query(10, ge=1, le=50)
):
    """Search documents using vector similarity"""
    
    try:
        # Perform vector search
        results = await document_service.search_similar_documents(
            query_text=query,
            limit=limit,
            document_type=document_type.value if document_type else None
        )
        
        return {
            "query": query,
            "results": results,
            "total_found": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        raise HTTPException(status_code=500, detail="Search failed")

@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[DocumentStatus] = None,
    document_type: Optional[DocumentType] = None,
    search: Optional[str] = Query(None, min_length=2),
    db: Session = Depends(get_db)
):
    """Enhanced document listing with search and filters"""
    
    query = db.query(Document)
    
    # Apply filters
    if status:
        query = query.filter(Document.status == status.value)
    
    if document_type:
        query = query.filter(Document.document_type == document_type.value)
    
    # Text search in filename and extracted text
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            Document.original_filename.ilike(search_term) |
            Document.extracted_text.ilike(search_term)
        )
    
    # Get total count
    total = query.count()
    
    # Get documents with pagination
    documents = query.order_by(Document.created_at.desc()).offset(skip).limit(limit).all()
    
    return DocumentListResponse(
        documents=[DocumentStatusResponse(**doc.to_dict()) for doc in documents],
        total=total,
        skip=skip,
        limit=limit,
        filters={
            "status": status.value if status else None,
            "document_type": document_type.value if document_type else None,
            "search": search
        }
    )

@router.delete("/{doc_id}")
async def delete_document(doc_id: str, db: Session = Depends(get_db)):
    """Delete document and all associated data"""
    
    try:
        result = await document_service.delete_document(doc_id, db)
        
        # Clear cache
        await cache_service.clear_document_cache(doc_id)
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting document {doc_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete document")

@router.post("/{doc_id}/reprocess")
async def reprocess_document(
    doc_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Reprocess a document (useful for testing or after improvements)"""
    
    document = db.query(Document).filter(Document.id == doc_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Reset status
    document.status = "uploaded"
    document.error_message = None
    document.retry_count = 0
    db.commit()
    
    # Clear cache
    await cache_service.clear_document_cache(doc_id)
    
    # Queue for reprocessing
    background_tasks.add_task(
        document_service.process_document_background,
        doc_id
    )
    
    return {
        "document_id": doc_id,
        "status": "queued_for_reprocessing",
        "message": "Document queued for reprocessing"
    }