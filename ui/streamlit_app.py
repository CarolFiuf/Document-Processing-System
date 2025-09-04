import streamlit as st
import requests
import time
import json
import pandas as pd
from typing import Dict, Any
import plotly.express as px
import plotly.graph_objects as go
import os

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
    st.markdown("*Personal MLOps Project - **Week 2: AI Intelligence Added** 🧠*")
    
    # Sidebar navigation
    with st.sidebar:
        st.header("📋 Navigation")
        page = st.selectbox(
            "Choose a page:",
            [
                "Upload Document", 
                "View Documents", 
                "Document Search",
                "Analytics Dashboard",
                "System Status"
            ]
        )
    
    # Page routing
    if page == "Upload Document":
        upload_page()
    elif page == "View Documents":
        view_documents_page()
    elif page == "Document Search":
        search_page()
    elif page == "Analytics Dashboard":
        analytics_page()
    elif page == "System Status":
        system_status_page()

def upload_page():
    st.header("📤 Upload Document")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # File uploader
        uploaded_file = st.file_uploader(
            "Choose a document",
            type=['pdf', 'jpg', 'jpeg', 'png', 'docx', 'doc'],
            help="Supported formats: PDF, JPG, PNG, DOCX, DOC"
        )
        
        # Document type selector
        doc_type = st.selectbox(
            "Document Type (Auto-detected if not specified)",
            ["", "contract", "invoice", "resume", "report", "letter", "other"]
        )
    
    with col2:
        st.markdown("### 🆕 Week 2 Features")
        st.info("""
        **AI Analysis Added:**
        - 🧠 LLM-powered document understanding
        - 📊 Structured data extraction  
        - 🔍 Vector-based similarity search
        - 💡 Smart recommendations
        """)
    
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
            process_document_enhanced(uploaded_file, doc_type)

def process_document_enhanced(uploaded_file, doc_type: str):
    """Enhanced document processing with AI analysis"""
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Upload file
        status_text.text("📤 Uploading document...")
        progress_bar.progress(10)
        
        files = {"file": uploaded_file}
        data = {"document_type": doc_type} if doc_type else {}
        
        upload_response = requests.post(
            f"{API_BASE_URL}/api/v1/documents/upload",
            files=files,
            data=data,
            timeout=120
        )
        
        if upload_response.status_code != 200:
            st.error(f"Upload failed: {upload_response.text}")
            return
        
        doc_data = upload_response.json()
        doc_id = doc_data["document_id"]
        detected_type = doc_data.get("document_type", "unknown")
        
        st.success(f"✅ Document uploaded! Detected type: **{detected_type}**")
        
        status_text.text("⚙️ Processing: OCR extraction...")
        progress_bar.progress(30)
        
        # Poll for processing status with enhanced display
        max_wait_time = 300  # 5 minutes for LLM processing
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
                status_text.text("✅ Processing completed!")
                
                # Show enhanced results
                show_enhanced_results(doc_id)
                return
                
            elif current_status == "failed":
                st.error(f"❌ Processing failed: {status_data.get('error_message', 'Unknown error')}")
                return
                
            elif current_status == "processing":
                # Simulate progress stages
                elapsed = time.time() - start_time
                if elapsed < 30:
                    progress_bar.progress(40)
                    status_text.text("🔍 OCR: Extracting text from document...")
                elif elapsed < 120:
                    progress_bar.progress(70)
                    status_text.text("🧠 AI Analysis: Understanding document content...")
                else:
                    progress_bar.progress(85)
                    status_text.text("🎯 Vector Processing: Creating embeddings...")
                
            time.sleep(3)
        
        st.warning("⏳ Processing taking longer than expected. Check 'View Documents' for updates.")
        
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def show_enhanced_results(doc_id: str):
    """Display enhanced processing results with AI analysis"""
    
    try:
        # Get complete results
        results_response = requests.get(
            f"{API_BASE_URL}/api/v1/documents/{doc_id}/results"
        )
        
        if results_response.status_code != 200:
            st.error("Failed to get results")
            return
        
        results = results_response.json()
        
        st.success("✅ Document processed successfully!")
        
        # Create tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Overview", 
            "🧠 AI Analysis", 
            "📝 Extracted Text", 
            "🔍 Similar Documents"
        ])
        
        with tab1:
            show_overview_tab(results)
        
        with tab2:
            show_ai_analysis_tab(results)
        
        with tab3:
            show_text_tab(results)
        
        with tab4:
            show_similar_documents_tab(doc_id)
        
    except Exception as e:
        st.error(f"Error displaying results: {str(e)}")

def show_overview_tab(results):
    """Show overview with key metrics"""
    
    metadata = results.get("metadata", {})
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "⏱️ Processing Time", 
            f"{metadata.get('processing_time_seconds', 0):.2f}s"
        )
    
    with col2:
        st.metric(
            "🎯 OCR Confidence", 
            f"{metadata.get('ocr_confidence', 0):.2%}"
        )
    
    with col3:
        st.metric(
            "📄 Pages", 
            metadata.get('pages_count', 1)
        )
    
    with col4:
        st.metric(
            "🌐 Language", 
            metadata.get('language_detected', 'Unknown')
        )
    
    # Document statistics
    extracted_text = results.get("extracted_text", "")
    if extracted_text:
        word_count = len(extracted_text.split())
        char_count = len(extracted_text)
        
        st.subheader("📈 Document Statistics")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📝 Words", f"{word_count:,}")
        with col2:
            st.metric("🔤 Characters", f"{char_count:,}")
        with col3:
            st.metric("💾 File Size", f"{metadata.get('file_size_bytes', 0):,} bytes")

def show_ai_analysis_tab(results):
    """Show AI analysis results"""
    
    llm_analysis = results.get("llm_analysis", {})
    
    if not llm_analysis or "error" in llm_analysis:
        st.warning("AI analysis not available or failed")
        return
    
    st.subheader("🧠 AI Document Analysis")
    
    # Document type and confidence
    doc_type = llm_analysis.get("document_type", "unknown")
    confidence = llm_analysis.get("confidence", 0)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("📋 Document Type", doc_type.title())
    with col2:
        st.metric("🎯 Analysis Confidence", f"{confidence:.2%}")
    
    # Summary
    summary = llm_analysis.get("summary", "")
    if summary:
        st.subheader("📝 Summary")
        st.info(summary)
    
    # Structured data based on document type
    if doc_type == "resume":
        show_resume_analysis(llm_analysis)
    elif doc_type == "contract":
        show_contract_analysis(llm_analysis)
    elif doc_type == "invoice":
        show_invoice_analysis(llm_analysis)
    else:
        show_general_analysis(llm_analysis)

def show_resume_analysis(analysis):
    """Show resume-specific analysis"""
    
    candidate_info = analysis.get("candidate_info", {})
    
    if candidate_info:
        st.subheader("👤 Candidate Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if candidate_info.get("name"):
                st.write(f"**Name:** {candidate_info['name']}")
            if candidate_info.get("email"):
                st.write(f"**Email:** {candidate_info['email']}")
            if candidate_info.get("phone"):
                st.write(f"**Phone:** {candidate_info['phone']}")
        
        with col2:
            if candidate_info.get("position_desired"):
                st.write(f"**Position:** {candidate_info['position_desired']}")
            if candidate_info.get("address"):
                st.write(f"**Address:** {candidate_info['address']}")
    
    # Experience
    experience = analysis.get("experience", [])
    if experience:
        st.subheader("💼 Work Experience")
        for exp in experience[:3]:  # Show top 3
            with st.expander(f"{exp.get('position', 'Unknown')} at {exp.get('company', 'Unknown')}"):
                st.write(f"**Duration:** {exp.get('start_date', '')} - {exp.get('end_date', '')}")
                if exp.get("responsibilities"):
                    st.write("**Responsibilities:**")
                    for resp in exp["responsibilities"][:3]:
                        st.write(f"• {resp}")
    
    # Skills
    skills = analysis.get("skills", {})
    if skills:
        st.subheader("🎯 Skills")
        
        if skills.get("technical"):
            st.write("**Technical Skills:**")
            st.write(", ".join(skills["technical"][:10]))
        
        if skills.get("languages"):
            st.write("**Languages:**")
            for lang in skills["languages"][:5]:
                if isinstance(lang, dict):
                    st.write(f"• {lang.get('language', 'Unknown')} ({lang.get('level', 'Unknown')})")
                else:
                    st.write(f"• {lang}")

def show_contract_analysis(analysis):
    """Show contract-specific analysis"""
    
    # Parties
    parties = analysis.get("parties", [])
    if parties:
        st.subheader("👥 Contract Parties")
        for i, party in enumerate(parties[:5], 1):
            st.write(f"**Party {i}:** {party}")
    
    # Key terms
    key_terms = analysis.get("key_terms", [])
    if key_terms:
        st.subheader("📋 Key Terms")
        for term in key_terms[:10]:
            st.write(f"• {term}")
    
    # Financial information
    financial_amounts = analysis.get("financial_amounts", [])
    if financial_amounts:
        st.subheader("💰 Financial Details")
        for amount in financial_amounts[:5]:
            if isinstance(amount, dict):
                st.write(f"• {amount.get('description', 'Amount')}: {amount.get('amount', 'Unknown')} {amount.get('currency', '')}")
            else:
                st.write(f"• {amount}")
    
    # Risk factors
    risk_factors = analysis.get("risk_factors", [])
    if risk_factors:
        st.subheader("⚠️ Risk Factors")
        for risk in risk_factors[:5]:
            st.warning(f"• {risk}")

def show_invoice_analysis(analysis):
    """Show invoice-specific analysis"""
    
    # Basic info
    col1, col2 = st.columns(2)
    
    with col1:
        if analysis.get("invoice_number"):
            st.write(f"**Invoice #:** {analysis['invoice_number']}")
        if analysis.get("date"):
            st.write(f"**Date:** {analysis['date']}")
        if analysis.get("due_date"):
            st.write(f"**Due Date:** {analysis['due_date']}")
    
    with col2:
        # Vendor info
        vendor = analysis.get("vendor", {})
        if vendor:
            st.write("**Vendor:**")
            if vendor.get("name"):
                st.write(f"• {vendor['name']}")
            if vendor.get("contact"):
                st.write(f"• {vendor['contact']}")
    
    # Totals
    totals = analysis.get("totals", {})
    if totals:
        st.subheader("💰 Invoice Totals")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if totals.get("subtotal"):
                st.metric("Subtotal", f"{totals.get('currency', '$')}{totals['subtotal']}")
        with col2:
            if totals.get("tax"):
                st.metric("Tax", f"{totals.get('currency', '$')}{totals['tax']}")
        with col3:
            if totals.get("total"):
                st.metric("**Total**", f"{totals.get('currency', '$')}{totals['total']}")

def show_general_analysis(analysis):
    """Show general document analysis"""
    
    # Key entities
    key_entities = analysis.get("key_entities", {})
    if key_entities:
        st.subheader("🏷️ Key Entities")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if key_entities.get("people"):
                st.write("**People:**")
                for person in key_entities["people"][:5]:
                    st.write(f"• {person}")
            
            if key_entities.get("organizations"):
                st.write("**Organizations:**")
                for org in key_entities["organizations"][:5]:
                    st.write(f"• {org}")
        
        with col2:
            if key_entities.get("dates"):
                st.write("**Dates:**")
                for date in key_entities["dates"][:5]:
                    st.write(f"• {date}")
            
            if key_entities.get("amounts"):
                st.write("**Amounts:**")
                for amount in key_entities["amounts"][:5]:
                    st.write(f"• {amount}")
    
    # Key points
    key_points = analysis.get("key_points", [])
    if key_points:
        st.subheader("🎯 Key Points")
        for point in key_points[:10]:
            st.write(f"• {point}")

def show_text_tab(results):
    """Show extracted text"""
    
    extracted_text = results.get("extracted_text", "")
    
    if extracted_text:
        st.subheader("📝 Extracted Text")
        
        # Show preview
        st.markdown("**Text Preview:**")
        preview_text = extracted_text[:1000] + "..." if len(extracted_text) > 1000 else extracted_text
        st.code(preview_text)
        
        # Show full text in expandable section
        with st.expander("View Full Text", expanded=False):
            st.text_area(
                "Complete extracted text:",
                value=extracted_text,
                height=400,
                disabled=True
            )
    else:
        st.warning("No text was extracted from the document.")

def show_similar_documents_tab(doc_id: str):
    """Show similar documents"""
    
    try:
        similar_response = requests.get(
            f"{API_BASE_URL}/api/v1/documents/{doc_id}/similar?limit=5"
        )
        
        if similar_response.status_code == 200:
            similar_data = similar_response.json()
            similar_docs = similar_data.get("similar_documents", [])
            
            if similar_docs:
                st.subheader("🔍 Similar Documents")
                
                for doc in similar_docs:
                    similarity_score = doc.get("similarity_score", 0)
                    
                    with st.expander(f"📄 Document {doc.get('document_id', 'Unknown')[:8]}... (Similarity: {similarity_score:.2%})"):
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            metadata = doc.get("metadata", {})
                            if metadata.get("document_type"):
                                st.write(f"**Type:** {metadata['document_type']}")
                            if metadata.get("filename"):
                                st.write(f"**Filename:** {metadata['filename']}")
                        
                        with col2:
                            st.write(f"**Similarity:** {similarity_score:.2%}")
                            if doc.get("chunk_index") is not None:
                                st.write(f"**Chunk:** {doc['chunk_index']}")
                        
                        # Preview text
                        preview = doc.get("text_preview", "")
                        if preview:
                            st.write("**Preview:**")
                            st.text(preview[:200] + "..." if len(preview) > 200 else preview)
            else:
                st.info("No similar documents found.")
        else:
            st.warning("Unable to find similar documents.")
            
    except Exception as e:
        st.error(f"Error finding similar documents: {e}")

def search_page():
    """Document search page"""
    st.header("🔍 Document Search")
    
    # Search input
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query = st.text_input(
            "Search documents:",
            placeholder="Enter keywords to search...",
            help="Search using natural language or specific terms"
        )
    
    with col2:
        document_type = st.selectbox(
            "Filter by type:",
            ["", "contract", "invoice", "resume", "report", "letter", "other"]
        )
    
    if st.button("🔍 Search", type="primary") and query:
        search_documents(query, document_type)

def search_documents(query: str, document_type: str = None):
    """Perform vector search"""
    
    try:
        params = {"query": query, "limit": 10}
        if document_type:
            params["document_type"] = document_type
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/documents/search",
            params=params
        )
        
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            
            if results:
                st.success(f"Found {len(results)} similar documents")
                
                for result in results:
                    similarity = result.get("similarity_score", 0)
                    
                    with st.expander(f"📄 Document (Similarity: {similarity:.2%})"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            metadata = result.get("metadata", {})
                            st.write(f"**ID:** {result.get('document_id', 'Unknown')}")
                            if metadata.get("document_type"):
                                st.write(f"**Type:** {metadata['document_type']}")
                            if metadata.get("filename"):
                                st.write(f"**File:** {metadata['filename']}")
                        
                        with col2:
                            st.metric("Similarity Score", f"{similarity:.2%}")
                        
                        preview = result.get("text_preview", "")
                        if preview:
                            st.write("**Preview:**")
                            st.text(preview)
            else:
                st.info("No documents found matching your search.")
        else:
            st.error("Search failed. Please try again.")
            
    except Exception as e:
        st.error(f"Search error: {e}")

def analytics_page():
    """Analytics dashboard"""
    st.header("📊 Analytics Dashboard")
    
    try:
        # Get analytics data (you'll need to implement this endpoint)
        response = requests.get(f"{API_BASE_URL}/api/v1/analytics/stats")
        
        if response.status_code == 200:
            stats = response.json()
            
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📄 Total Documents", stats.get("total_documents", 0))
            
            with col2:
                st.metric("✅ Completed", stats.get("completed_documents", 0))
            
            with col3:
                st.metric("⏱️ Avg Processing", f"{stats.get('average_processing_time', 0):.2f}s")
            
            with col4:
                st.metric("❌ Failed", stats.get("failed_documents", 0))
            
            # Charts
            col1, col2 = st.columns(2)
            
            with col1:
                # Document types pie chart
                if stats.get("documents_by_type"):
                    fig = px.pie(
                        values=list(stats["documents_by_type"].values()),
                        names=list(stats["documents_by_type"].keys()),
                        title="Documents by Type"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Languages bar chart
                if stats.get("documents_by_language"):
                    fig = px.bar(
                        x=list(stats["documents_by_language"].keys()),
                        y=list(stats["documents_by_language"].values()),
                        title="Documents by Language"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.info("Analytics data not available")
    
    except Exception as e:
        st.error(f"Error loading analytics: {e}")

def view_documents_page():
    """Enhanced document library with filters"""
    st.header("📚 Document Library")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox(
            "Status:",
            ["", "uploaded", "processing", "completed", "failed"]
        )
    
    with col2:
        type_filter = st.selectbox(
            "Type:",
            ["", "contract", "invoice", "resume", "report", "letter", "other"]
        )
    
    with col3:
        search_term = st.text_input("Search:", placeholder="Filename or content...")
    
    try:
        # Build query parameters
        params = {"limit": 50}
        if status_filter:
            params["status"] = status_filter
        if type_filter:
            params["document_type"] = type_filter
        if search_term:
            params["search"] = search_term
        
        response = requests.get(f"{API_BASE_URL}/api/v1/documents/", params=params)
        
        if response.status_code != 200:
            st.error("Failed to load documents")
            return
        
        data = response.json()
        documents = data.get("documents", [])
        total = data.get("total", 0)
        
        if not documents:
            st.info("No documents found. Upload your first document!")
            return
        
        st.info(f"Found {total} documents")
        
        # Display documents in a more organized way
        for doc in documents:
            with st.expander(f"📄 {doc['filename']} - **{doc['status'].upper()}**", expanded=False):
                
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.write("**Document Info:**")
                    st.write(f"• ID: `{doc['id'][:8]}...`")
                    st.write(f"• Type: {doc.get('document_type', 'Unknown')}")
                    st.write(f"• Size: {doc.get('file_size_bytes', 0):,} bytes")
                    st.write(f"• Status: **{doc['status']}**")
                
                with col2:
                    st.write("**Processing Info:**")
                    created = doc.get('created_at', 'Unknown')
                    if created != 'Unknown':
                        try:
                            from datetime import datetime
                            dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                            created = dt.strftime('%Y-%m-%d %H:%M')
                        except:
                            pass
                    st.write(f"• Created: {created}")
                    st.write(f"• Time: {doc.get('processing_time_seconds', 0):.2f}s")
                    st.write(f"• Confidence: {doc.get('ocr_confidence', 0):.2%}")
                    st.write(f"• Pages: {doc.get('pages_count', 'Unknown')}")
                
                with col3:
                    # Action buttons
                    if st.button(f"🔍 View", key=f"view_{doc['id']}"):
                        if doc['status'] == 'completed':
                            show_enhanced_results(doc['id'])
                        else:
                            st.warning(f"Document is {doc['status']}")
                    
                    if st.button(f"🔄 Refresh", key=f"refresh_{doc['id']}"):
                        st.rerun()
                    
                    if st.button(f"🗑️ Delete", key=f"delete_{doc['id']}", type="secondary"):
                        delete_document(doc['id'])
        
    except Exception as e:
        st.error(f"Error loading documents: {str(e)}")

def system_status_page():
    """Enhanced system status with all services"""
    st.header("⚡ System Status")
    
    # Create columns for different services
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔧 Core Services")
        
        # API Health
        try:
            health_response = requests.get(f"{API_BASE_URL}/health", timeout=5)
            if health_response.status_code == 200:
                st.success("✅ API Server - Healthy")
            else:
                st.error("❌ API Server - Unhealthy")
        except:
            st.error("❌ API Server - Cannot connect")
        
        # Database check
        try:
            detailed_response = requests.get(f"{API_BASE_URL}/api/v1/health/detailed", timeout=5)
            if detailed_response.status_code == 200:
                health_data = detailed_response.json()
                checks = health_data.get("checks", {})
                
                # Database
                if checks.get("database") == "healthy":
                    st.success("✅ PostgreSQL - Connected")
                else:
                    st.error("❌ PostgreSQL - Connection failed")
                
                # File system
                if checks.get("file_system") == "healthy":
                    st.success("✅ File System - Accessible")
                else:
                    st.error("❌ File System - Access failed")
            else:
                st.warning("⚠️ Detailed health check unavailable")
        except:
            st.warning("⚠️ Cannot perform detailed health check")
    
    with col2:
        st.subheader("🧠 AI Services")
        
        # vLLM check
        try:
            vllm_response = requests.get("http://localhost:8001/health", timeout=5)
            if vllm_response.status_code == 200:
                st.success("✅ vLLM Server - Ready")
            else:
                st.error("❌ vLLM Server - Not responding")
        except:
            st.error("❌ vLLM Server - Cannot connect")
        
        # Redis check
        st.info("🔄 Redis - Status check via API")
        
        # Milvus check  
        st.info("🔍 Milvus - Status check via API")
    
    # System metrics
    st.subheader("📊 System Metrics")
    
    try:
        metrics_response = requests.get(f"{API_BASE_URL}/metrics", timeout=5)
        
        if metrics_response.status_code == 200:
            with st.expander("View Raw Metrics", expanded=False):
                st.code(metrics_response.text[:2000] + "..." if len(metrics_response.text) > 2000 else metrics_response.text)
        else:
            st.info("Metrics endpoint not available")
            
    except:
        st.info("Cannot connect to metrics endpoint")

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

if __name__ == "__main__":
    main()