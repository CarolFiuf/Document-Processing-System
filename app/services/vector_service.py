# app/services/vector_service.py - New service for semantic search
import logging
import numpy as np
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility
import uuid
import json

from app.config import settings

logger = logging.getLogger(__name__)

class VectorService:
    def __init__(self):
        """Initialize vector service với Milvus và SentenceTransformer"""
        
        # Initialize sentence transformer for embeddings
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')  # Lightweight, good performance
        self.embedding_dim = 384  # Dimension of all-MiniLM-L6-v2
        
        # Milvus collection name
        self.collection_name = "document_embeddings"
        
        # Initialize Milvus connection
        self._init_milvus_connection()
        self._ensure_collection_exists()
        
        logger.info("Vector service initialized successfully")
    
    def _init_milvus_connection(self):
        """Initialize connection to Milvus"""
        try:
            connections.connect(
                alias="default",
                host=settings.milvus_host,
                port=settings.milvus_port
            )
            logger.info(f"Connected to Milvus at {settings.milvus_host}:{settings.milvus_port}")
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            raise e
    
    def _ensure_collection_exists(self):
        """Create collection if it doesn't exist"""
        
        if utility.has_collection(self.collection_name):
            self.collection = Collection(self.collection_name)
            logger.info(f"Using existing collection: {self.collection_name}")
            return
        
        # Define collection schema
        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=100, is_primary=True),
            FieldSchema(name="document_id", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="text_chunk", dtype=DataType.VARCHAR, max_length=5000),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.embedding_dim),
            FieldSchema(name="metadata", dtype=DataType.VARCHAR, max_length=2000),
            FieldSchema(name="chunk_index", dtype=DataType.INT64)
        ]
        
        schema = CollectionSchema(fields, f"Document embeddings for {self.collection_name}")
        
        # Create collection
        self.collection = Collection(self.collection_name, schema)
        
        # Create index for vector search
        index_params = {
            "metric_type": "IP",  # Inner Product
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128}
        }
        
        self.collection.create_index("embedding", index_params)
        
        logger.info(f"Created new collection: {self.collection_name}")
    
    async def create_document_embedding(
        self,
        doc_id: str,
        text: str,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create embeddings for a document"""
        
        try:
            # Split text into chunks (for long documents)
            text_chunks = self._split_text(text, max_chunk_size=1000)
            
            embeddings_data = []
            
            for i, chunk in enumerate(text_chunks):
                # Create embedding
                embedding = self.embedding_model.encode(chunk)
                
                # Prepare data for insertion
                chunk_id = f"{doc_id}_chunk_{i}"
                chunk_data = {
                    "id": chunk_id,
                    "document_id": doc_id,
                    "text_chunk": chunk,
                    "embedding": embedding.tolist(),
                    "metadata": json.dumps(metadata or {}),
                    "chunk_index": i
                }
                
                embeddings_data.append(chunk_data)
            
            # Insert into Milvus
            self.collection.insert(embeddings_data)
            
            # Flush to ensure data is written
            self.collection.flush()
            
            logger.info(f"Created {len(embeddings_data)} embeddings for document {doc_id}")
            
            return {
                "document_id": doc_id,
                "chunks_created": len(embeddings_data),
                "embedding_dimension": self.embedding_dim,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error creating embeddings for document {doc_id}: {e}")
            raise e
    
    async def search_similar_documents(
        self,
        query_text: str,
        limit: int = 5,
        filter_metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar documents using vector similarity"""
        
        try:
            # Create query embedding
            query_embedding = self.embedding_model.encode(query_text)
            
            # Search parameters
            search_params = {
                "metric_type": "IP",
                "params": {"nprobe": 10}
            }
            
            # Load collection for search
            self.collection.load()
            
            # Perform search
            search_results = self.collection.search(
                data=[query_embedding.tolist()],
                anns_field="embedding",
                param=search_params,
                limit=limit * 2,  # Get more results to filter by document
                output_fields=["document_id", "text_chunk", "metadata", "chunk_index"]
            )
            
            # Process results
            similar_docs = []
            seen_documents = set()
            
            for hits in search_results:
                for hit in hits:
                    doc_id = hit.entity.get("document_id")
                    
                    # Skip if we already have this document
                    if doc_id in seen_documents:
                        continue
                    
                    seen_documents.add(doc_id)
                    
                    # Parse metadata
                    try:
                        metadata = json.loads(hit.entity.get("metadata", "{}"))
                    except:
                        metadata = {}
                    
                    similar_doc = {
                        "document_id": doc_id,
                        "similarity_score": hit.score,
                        "text_preview": hit.entity.get("text_chunk", "")[:200] + "...",
                        "metadata": metadata,
                        "chunk_index": hit.entity.get("chunk_index", 0)
                    }
                    
                    similar_docs.append(similar_doc)
                    
                    if len(similar_docs) >= limit:
                        break
            
            logger.info(f"Found {len(similar_docs)} similar documents")
            return similar_docs
            
        except Exception as e:
            logger.error(f"Error searching similar documents: {e}")
            return []
    
    def _split_text(self, text: str, max_chunk_size: int = 1000) -> List[str]:
        """Split text into chunks for embedding"""
        
        if len(text) <= max_chunk_size:
            return [text]
        
        # Split by sentences first
        sentences = text.replace('\n', ' ').split('. ')
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # Check if adding this sentence would exceed chunk size
            if len(current_chunk + sentence) > max_chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = sentence
                else:
                    # Sentence is too long, split by words
                    words = sentence.split()
                    while words:
                        temp_chunk = ""
                        while words and len(temp_chunk + words[0]) < max_chunk_size:
                            temp_chunk += words.pop(0) + " "
                        if temp_chunk:
                            chunks.append(temp_chunk.strip())
            else:
                current_chunk += sentence + ". "
        
        # Add remaining chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    async def get_document_embeddings_stats(self, doc_id: str) -> Dict[str, Any]:
        """Get statistics about document embeddings"""
        
        try:
            # Load collection
            self.collection.load()
            
            # Query for document chunks
            expr = f'document_id == "{doc_id}"'
            results = self.collection.query(
                expr=expr,
                output_fields=["id", "chunk_index", "metadata"]
            )
            
            return {
                "document_id": doc_id,
                "total_chunks": len(results),
                "chunk_indices": [r["chunk_index"] for r in results],
                "embedding_dimension": self.embedding_dim
            }
            
        except Exception as e:
            logger.error(f"Error getting embedding stats for document {doc_id}: {e}")
            return {"error": str(e)}
    
    async def delete_document_embeddings(self, doc_id: str) -> Dict[str, Any]:
        """Delete all embeddings for a document"""
        
        try:
            # Delete from Milvus
            expr = f'document_id == "{doc_id}"'
            self.collection.delete(expr)
            
            logger.info(f"Deleted embeddings for document {doc_id}")
            
            return {
                "document_id": doc_id,
                "status": "deleted"
            }
            
        except Exception as e:
            logger.error(f"Error deleting embeddings for document {doc_id}: {e}")
            return {"error": str(e)}