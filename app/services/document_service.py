# app/services/document_service.py - Updated with LLM integration
import asyncio
import time
import logging
import uuid
import os
import json
from pathlib import Path
from sqlalchemy.orm import Session
from fastapi import UploadFile
from datetime import datetime
from typing import List, Dict, Any

from app.models.database import Document
from app.processors.ocr_processor import OCRProcessor
from app.processors.llm_processor import LLMProcessor
from app.services.vector_service import VectorService
from app.config import settings
from app.utils.file_utils import save_uploaded_file, cleanup_file

logger = logging.getLogger(__name__)

class DocumentService:
    def __init__(self):
        self.ocr_processor = OCRProcessor()
        self.llm_processor = LLMProcessor()
        self.vector_service = VectorService()
    
    async def upload_document(
        self, 
        file: UploadFile, 
        document_type: str = None, 
        db: Session = None
    ) -> dict:
        """Upload and save document - enhanced version"""
        
        # Generate unique document ID
        doc_id = str(uuid.uuid4())
        file_extension = Path(file.filename).suffix
        filename = f"{doc_id}{file_extension}"
        file_path = os.path.join(settings.upload_path, filename)
        
        try:
            # Save file
            await save_uploaded_file(file, file_path)
            file_size = os.path.getsize(file_path)
            
            # Auto-detect document type if not provided (defer to background processing)
            if not document_type:
                document_type = "other"  # Default type, will be detected during background processing
            
            # Create database record
            document = Document(
                id=doc_id,
                filename=filename,
                original_filename=file.filename,
                file_path=file_path,
                file_size_bytes=file_size,
                document_type=document_type,
                status="uploaded"
            )
            
            db.add(document)
            db.commit()
            
            logger.info(f"Document uploaded: {doc_id} (type: {document_type})")
            
            return {
                "document_id": doc_id,
                "filename": file.filename,
                "status": "uploaded",
                "file_size_bytes": file_size,
                "document_type": document_type,
                "message": "Document uploaded successfully and queued for processing"
            }
            
        except Exception as e:
            # Cleanup file if database operation fails
            cleanup_file(file_path)
            logger.error(f"Error uploading document: {e}")
            raise e
    
    async def process_document(self, doc_id: str, db: Session) -> dict:
        """Enhanced document processing pipeline with LLM analysis"""
        
        try:
            # Get document from database
            document = db.query(Document).filter(Document.id == doc_id).first()
            if not document:
                raise ValueError(f"Document {doc_id} not found")
            
            logger.info(f"Starting enhanced processing for document {doc_id}")
            
            # Update status to processing
            document.status = "processing"
            document.updated_at = datetime.utcnow()
            db.commit()
            
            start_time = time.time()
            
            # Step 1: Extract text using OCR (existing)
            logger.info(f"Step 1: OCR extraction from {document.file_path}")
            ocr_result = await self.ocr_processor.extract_text(document.file_path)
            extracted_text = ocr_result.get('text', '')
            
            # Step 1.5: Detect document type if not already determined
            if document.document_type == "other":
                logger.info(f"Step 1.5: Detecting document type")
                detected_type = self.llm_processor._detect_document_type(extracted_text)
                document.document_type = detected_type
                db.commit()
                logger.info(f"Document type detected: {detected_type}")
            
            # Step 2: LLM Analysis (NEW!)
            logger.info(f"Step 2: LLM analysis")
            llm_analysis = await self.llm_processor.analyze_document(
                text=extracted_text,
                document_type=document.document_type,
                additional_context={
                    "filename": document.original_filename,
                    "file_size": document.file_size_bytes
                }
            )
            
            # Step 3: Vector embedding creation (NEW!)
            logger.info(f"Step 3: Creating vector embeddings")
            embedding_result = await self.vector_service.create_document_embedding(
                doc_id=doc_id,
                text=extracted_text,
                metadata={
                    "document_type": document.document_type,
                    "filename": document.original_filename,
                    "llm_analysis": llm_analysis
                }
            )
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Update document with results
            document.extracted_text = extracted_text
            document.ocr_confidence = ocr_result.get('confidence', 0.0)
            document.processing_time_seconds = processing_time
            document.pages_count = ocr_result.get('pages_count', 1)
            document.language_detected = ocr_result.get('language', 'unknown')
            document.llm_analysis = json.dumps(llm_analysis)  # Store as JSON string
            document.status = "completed"
            
            db.commit()
            
            logger.info(f"Document {doc_id} processed successfully in {processing_time:.2f}s")
            
            return {
                "document_id": doc_id,
                "status": "completed",
                "processing_time": processing_time,
                "ocr_results": {
                    "text_length": len(extracted_text),
                    "confidence": ocr_result.get('confidence', 0.0),
                    "language": ocr_result.get('language', 'unknown')
                },
                "llm_analysis": llm_analysis,
                "vector_embedding": embedding_result
            }
            
        except Exception as e:
            logger.error(f"Error processing document {doc_id}: {str(e)}")
            
            # Update status to failed
            document.status = "failed"
            document.error_message = str(e)
            document.retry_count += 1
            db.commit()
            
            raise e
    
    async def search_similar_documents(
        self, 
        query_text: str, 
        limit: int = 5,
        document_type: str = None
    ) -> List[Dict[str, Any]]:
        """Search for similar documents using vector similarity"""
        
        try:
            # Use vector service to find similar documents
            similar_docs = await self.vector_service.search_similar_documents(
                query_text=query_text,
                limit=limit,
                filter_metadata={"document_type": document_type} if document_type else None
            )
            
            return similar_docs
            
        except Exception as e:
            logger.error(f"Error searching similar documents: {e}")
            return []
    
    async def get_document_insights(self, doc_id: str, db: Session) -> Dict[str, Any]:
        """Get comprehensive insights for a document"""
        
        try:
            # Get document
            document = db.query(Document).filter(Document.id == doc_id).first()
            if not document:
                raise ValueError(f"Document {doc_id} not found")
            
            # Parse LLM analysis
            llm_analysis = {}
            if document.llm_analysis:
                try:
                    llm_analysis = json.loads(document.llm_analysis)
                except json.JSONDecodeError:
                    llm_analysis = {"raw": document.llm_analysis}
            
            # Find similar documents
            similar_docs = []
            if document.extracted_text:
                similar_docs = await self.search_similar_documents(
                    query_text=document.extracted_text[:500],  # Use first 500 chars
                    limit=3,
                    document_type=document.document_type
                )
            
            # Compile comprehensive insights
            insights = {
                "document_info": {
                    "id": document.id,
                    "filename": document.original_filename,
                    "type": document.document_type,
                    "status": document.status,
                    "created_at": document.created_at.isoformat() if document.created_at else None
                },
                "processing_results": {
                    "ocr_confidence": document.ocr_confidence,
                    "processing_time": document.processing_time_seconds,
                    "pages_count": document.pages_count,
                    "language_detected": document.language_detected,
                    "text_length": len(document.extracted_text or "")
                },
                "llm_analysis": llm_analysis,
                "similar_documents": similar_docs,
                "recommendations": self._generate_recommendations(llm_analysis, document.document_type)
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Error getting document insights: {e}")
            raise e
    
    def _generate_recommendations(self, llm_analysis: Dict[str, Any], document_type: str) -> List[str]:
        """Generate recommendations based on LLM analysis"""
        
        recommendations = []
        
        if document_type == "resume":
            if llm_analysis.get("years_experience", 0) < 2:
                recommendations.append("Consider highlighting education and projects more prominently")
            if not llm_analysis.get("candidate_info", {}).get("email"):
                recommendations.append("Ensure contact information is clearly visible")
                
        elif document_type == "contract":
            if llm_analysis.get("risk_factors"):
                recommendations.append("Review identified risk factors carefully")
            if not llm_analysis.get("expiry_date"):
                recommendations.append("Consider adding clear contract expiry dates")
                
        elif document_type == "invoice":
            if not llm_analysis.get("due_date"):
                recommendations.append("Ensure payment due date is clearly specified")
                
        # General recommendations
        if llm_analysis.get("confidence", 0) < 0.7:
            recommendations.append("Document quality could be improved for better analysis")
        
        return recommendations
    
    async def process_document_background(self, doc_id: str):
        """Background task to process document with OCR and LLM analysis"""
        from app.database.session import get_db
        
        # Get database session
        db = next(get_db())
        
        try:
            # Get document
            document = db.query(Document).filter(Document.id == doc_id).first()
            if not document:
                logger.error(f"Document {doc_id} not found for background processing")
                return
            
            logger.info(f"Starting background processing for document {doc_id}")
            
            # Process the document
            await self.process_document(doc_id, db)
            
            logger.info(f"Background processing completed for document {doc_id}")
            
        except Exception as e:
            logger.error(f"Error in background processing for document {doc_id}: {e}")
        finally:
            db.close()