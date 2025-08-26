import streamlit as st
import requests
import time
import json
import os
from typing import Dict, Any

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Page config
st.set_page_config(
    page_title="Document Processing System",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.title("📄 Document Processing System")
    st.markdown("*Personal MLOps Project - Week 1 MVP*")
    
    # Sidebar navigation
    with st.sidebar:
        st.header("📋 Navigation")
        page = st.selectbox(
            "Choose a page:",
            ["Upload Document", "View Documents", "System Status"]
        )
    
    # Page routing
    if page == "Upload Document":
        upload_page()
    elif page == "View Documents":
        view_documents_page()
    elif page == "System Status":
        system_status_page()

def upload_page():
    st.header("📤 Upload Document")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a document",
        type=['pdf', 'jpg', 'jpeg', 'png', 'docx', 'doc'],
        help="Supported formats: PDF, JPG, PNG, DOCX, DOC"
    )
    
    # Document type selector
    doc_type = st.selectbox(
        "Document Type (Optional)",
        ["", "contract", "invoice", "report", "letter", "other"]
    )
    
    if uploaded_file is not None:
        # Display file info
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("File Name", uploaded_file.name)
        with col2:
            st.metric("File Size", f"{uploaded_file.size:,} bytes")
        with col3:
            st.metric("File Type", uploaded_file.type or "Unknown")
        
        # Process button
        if st.button("🚀 Process Document", type="primary"):
            process_document(uploaded_file, doc_type)

def process_document(uploaded_file, doc_type: str):
    """Process uploaded document"""
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Upload file
        status_text.text("Uploading document...")
        progress_bar.progress(20)
        
        files = {"file": uploaded_file}
        data = {"document_type": doc_type} if doc_type else {}
        
        upload_response = requests.post(
            f"{API_BASE_URL}/api/v1/documents/upload",
            files=files,
            data=data,
            timeout=60
        )
        
        if upload_response.status_code != 200:
            st.error(f"Upload failed: {upload_response.text}")
            return
        
        doc_data = upload_response.json()
        doc_id = doc_data["document_id"]
        
        status_text.text("Document uploaded! Processing...")
        progress_bar.progress(40)
        
        # Poll for status
        max_wait_time = 180  # 3 minutes
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            status_response = requests.get(
                f"{API_BASE_URL}/api/v1/documents/{doc_id}/status"
            )
            
            if status_response.status_code != 200:
                st.error("Failed to check status")
                return
            
            status_data = status_response.json()
            current_status = status_data["status"]
            
            if current_status == "completed":
                progress_bar.progress(100)
                status_text.text("Processing completed!")
                show_processing_results(doc_id)
                return
                
            elif current_status == "failed":
                st.error(f"Processing failed: {status_data.get('error_message', 'Unknown error')}")
                return
                
            elif current_status == "processing":
                progress_bar.progress(60)
                status_text.text("Processing document...")
                
            time.sleep(3)
        
        st.warning("Processing timeout. Check 'View Documents' for updates.")
        
    except Exception as e:
        st.error(f"Error: {str(e)}")

def show_processing_results(doc_id: str):
    """Display processing results"""
    
    try:
        results_response = requests.get(
            f"{API_BASE_URL}/api/v1/documents/{doc_id}/results"
        )
        
        if results_response.status_code != 200:
            st.error("Failed to get results")
            return
        
        results = results_response.json()
        
        st.success("✅ Document processed successfully!")
        
        # Display metadata
        st.subheader("📊 Processing Metadata")
        metadata = results.get("metadata", {})
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Processing Time", 
                f"{metadata.get('processing_time_seconds', 0):.2f}s"
            )
        
        with col2:
            st.metric(
                "OCR Confidence", 
                f"{metadata.get('ocr_confidence', 0):.2%}"
            )
        
        with col3:
            st.metric(
                "Pages Count", 
                metadata.get('pages_count', 1)
            )
        
        with col4:
            st.metric(
                "Language", 
                metadata.get('language_detected', 'Unknown')
            )
        
        # Display extracted text
        st.subheader("📝 Extracted Text")
        extracted_text = results.get("extracted_text", "")
        
        if extracted_text:
            word_count = len(extracted_text.split())
            char_count = len(extracted_text)
            
            st.info(f"📊 Statistics: {word_count:,} words, {char_count:,} characters")
            
            with st.expander("View Full Text", expanded=False):
                st.text_area(
                    "Extracted Text:",
                    value=extracted_text,
                    height=400,
                    disabled=True
                )
            
            # Show preview
            st.markdown("**Text Preview:**")
            preview = extracted_text[:1000] + "..." if len(extracted_text) > 1000 else extracted_text
            st.code(preview)
        else:
            st.warning("No text was extracted from the document.")
        
    except Exception as e:
        st.error(f"Error displaying results: {str(e)}")

def view_documents_page():
    st.header("📚 Document Library")
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/documents/")
        
        if response.status_code != 200:
            st.error("Failed to load documents")
            return
        
        data = response.json()
        documents = data.get("documents", [])
        
        if not documents:
            st.info("No documents found. Upload your first document!")
            return
        
        st.info(f"Found {len(documents)} documents")
        
        for doc in documents:
            with st.expander(f"📄 {doc['filename']} - {doc['status'].upper()}", expanded=False):
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Document Info:**")
                    st.write(f"• ID: `{doc['id']}`")
                    st.write(f"• Type: {doc.get('document_type', 'Unknown')}")
                    st.write(f"• Size: {doc.get('file_size_bytes', 0):,} bytes")
                    st.write(f"• Status: **{doc['status']}**")
                
                with col2:
                    st.write("**Processing Info:**")
                    st.write(f"• Created: {doc.get('created_at', 'Unknown')}")
                    st.write(f"• Processing Time: {doc.get('processing_time_seconds', 0):.2f}s")
                    st.write(f"• OCR Confidence: {doc.get('ocr_confidence', 0):.2%}")
                    st.write(f"• Pages: {doc.get('pages_count', 'Unknown')}")
                
                # Action buttons
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button(f"🔍 View Results", key=f"view_{doc['id']}"):
                        if doc['status'] == 'completed':
                            show_processing_results(doc['id'])
                        else:
                            st.warning(f"Document is {doc['status']}")
                
                with col2:
                    if st.button(f"🔄 Refresh", key=f"refresh_{doc['id']}"):
                        st.rerun()
                
                with col3:
                    if st.button(f"🗑️ Delete", key=f"delete_{doc['id']}", type="secondary"):
                        delete_document(doc['id'])
        
    except Exception as e:
        st.error(f"Error loading documents: {str(e)}")

def delete_document(doc_id: str):
    """Delete a document"""
    try:
        response = requests.delete(f"{API_BASE_URL}/api/v1/documents/{doc_id}")
        
        if response.status_code == 200:
            st.success("Document deleted!")
            st.rerun()
        else:
            st.error("Failed to delete document")
            
    except Exception as e:
        st.error(f"Error: {str(e)}")

def system_status_page():
    st.header("⚡ System Status")
    
    try:
        health_response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        
        if health_response.status_code == 200:
            st.success("✅ API is healthy")
            st.json(health_response.json())
        else:
            st.error("❌ API unhealthy")
        
        # Detailed health check
        try:
            detailed_response = requests.get(f"{API_BASE_URL}/api/v1/health/detailed", timeout=5)
            if detailed_response.status_code == 200:
                st.subheader("🔍 Detailed Health Check")
                st.json(detailed_response.json())
        except:
            pass
        
    except Exception as e:
        st.error(f"❌ Cannot connect to API: {str(e)}")

if __name__ == "__main__":
    main()