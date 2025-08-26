# app/processors/llm_processor.py
import openai
import json
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.config import settings

logger = logging.getLogger(__name__)

class LLMProcessor:
    def __init__(self):
        """Initialize LLM processor với vLLM OpenAI-compatible API"""
        self.client = openai.OpenAI(
            base_url=settings.llm_api_base,  # http://localhost:8001/v1
            api_key="dummy"  # vLLM doesn't need real API key
        )
        self.model_name = settings.llm_model_name
        logger.info(f"LLM processor initialized with model: {self.model_name}")
    
    async def analyze_document(
        self, 
        text: str, 
        document_type: str = None,
        additional_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Main document analysis with LLM"""
        
        if not text or len(text.strip()) < 10:
            return {"error": "Text too short for analysis"}
        
        try:
            # Create analysis prompt based on document type
            prompt = self._create_analysis_prompt(text, document_type, additional_context)
            
            start_time = time.time()
            
            # Call vLLM
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are an expert document analyst. Analyze documents accurately and extract structured information."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1024,
                temperature=0.1,  # Low temperature for consistent analysis
                top_p=0.9
            )
            
            processing_time = time.time() - start_time
            
            # Extract response
            analysis_text = response.choices[0].message.content
            
            # Try to parse as JSON, fallback to structured text
            try:
                analysis_result = json.loads(analysis_text)
            except json.JSONDecodeError:
                # Fallback: extract structured information from text
                analysis_result = self._parse_unstructured_response(analysis_text)
            
            # Add metadata
            analysis_result.update({
                "processing_time_seconds": processing_time,
                "model_used": self.model_name,
                "timestamp": datetime.now().isoformat(),
                "confidence": self._calculate_confidence(analysis_result),
                "document_type_detected": self._detect_document_type(text)
            })
            
            logger.info(f"Document analyzed in {processing_time:.2f}s")
            return analysis_result
            
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return {
                "error": f"Analysis failed: {str(e)}",
                "fallback_analysis": self._basic_fallback_analysis(text)
            }
    
    def _create_analysis_prompt(
        self, 
        text: str, 
        document_type: str = None, 
        additional_context: Dict[str, Any] = None
    ) -> str:
        """Create analysis prompt based on document type"""
        
        # Truncate text if too long (keep first 3000 chars for context)
        if len(text) > 3000:
            text = text[:3000] + "..."
        
        base_prompt = f"""
Analyze the following document and extract structured information in JSON format.

Document Type: {document_type or 'Unknown'}
Document Content:
{text}

Please extract the following information in JSON format:
"""
        
        if document_type == "contract":
            specific_instructions = """
{
    "document_type": "contract",
    "parties": ["Party 1", "Party 2"],
    "contract_date": "YYYY-MM-DD or null",
    "expiry_date": "YYYY-MM-DD or null",
    "key_terms": ["term1", "term2"],
    "financial_amounts": [{"amount": "value", "currency": "USD", "description": "purpose"}],
    "obligations": {
        "party1": ["obligation1", "obligation2"],
        "party2": ["obligation1", "obligation2"]
    },
    "important_dates": [{"date": "YYYY-MM-DD", "event": "description"}],
    "summary": "Brief contract summary",
    "risk_factors": ["risk1", "risk2"]
}
"""
        elif document_type == "invoice":
            specific_instructions = """
{
    "document_type": "invoice",
    "invoice_number": "INV-XXXX",
    "date": "YYYY-MM-DD",
    "due_date": "YYYY-MM-DD", 
    "vendor": {
        "name": "Company Name",
        "address": "Full Address",
        "contact": "Email/Phone"
    },
    "client": {
        "name": "Company Name", 
        "address": "Full Address",
        "contact": "Email/Phone"
    },
    "items": [
        {
            "description": "Item description",
            "quantity": 1,
            "unit_price": 100.00,
            "total": 100.00
        }
    ],
    "totals": {
        "subtotal": 100.00,
        "tax": 10.00,
        "total": 110.00,
        "currency": "USD"
    },
    "payment_terms": "Payment terms",
    "summary": "Invoice summary"
}
"""
        elif document_type in ["resume", "cv"] or "résumé" in text.lower() or "curriculum vitae" in text.lower():
            specific_instructions = """
{
    "document_type": "resume",
    "candidate_info": {
        "name": "Full Name",
        "email": "email@example.com",
        "phone": "+1-xxx-xxx-xxxx",
        "address": "Address",
        "position_desired": "Target Position"
    },
    "experience": [
        {
            "company": "Company Name",
            "position": "Job Title", 
            "start_date": "MM/YYYY",
            "end_date": "MM/YYYY or Present",
            "responsibilities": ["responsibility1", "responsibility2"],
            "achievements": ["achievement1", "achievement2"]
        }
    ],
    "education": [
        {
            "institution": "University Name",
            "degree": "Degree Type",
            "field": "Field of Study",
            "graduation_date": "YYYY",
            "gpa": "GPA if mentioned"
        }
    ],
    "skills": {
        "technical": ["skill1", "skill2"],
        "languages": [{"language": "English", "level": "Native"}],
        "other": ["skill1", "skill2"]
    },
    "summary": "Professional summary",
    "years_experience": 5
}
"""
        else:
            # General document analysis
            specific_instructions = """
{
    "document_type": "general",
    "main_topic": "Document main topic",
    "key_entities": {
        "people": ["Person 1", "Person 2"],
        "organizations": ["Company 1", "Company 2"], 
        "dates": ["2023-01-01", "2023-12-31"],
        "amounts": ["$1000", "€500"],
        "locations": ["City, Country"]
    },
    "summary": "Document summary in 2-3 sentences",
    "key_points": ["point1", "point2", "point3"],
    "action_items": ["action1", "action2"],
    "sentiment": "positive/negative/neutral",
    "urgency": "high/medium/low",
    "category": "business/legal/personal/technical"
}
"""
        
        return base_prompt + specific_instructions + "\n\nRespond only with valid JSON."
    
    def _parse_unstructured_response(self, response_text: str) -> Dict[str, Any]:
        """Parse unstructured LLM response into structured format"""
        
        # Basic fallback parsing
        lines = response_text.split('\n')
        
        result = {
            "analysis_text": response_text,
            "extracted_info": {},
            "summary": "",
            "parsing_method": "fallback"
        }
        
        # Try to extract key-value pairs
        for line in lines:
            if ':' in line and len(line.split(':')) == 2:
                key, value = line.split(':', 1)
                key = key.strip().lower().replace(' ', '_')
                value = value.strip()
                if value:
                    result["extracted_info"][key] = value
        
        # Extract summary (first few sentences)
        if len(response_text) > 100:
            sentences = response_text.split('.')[:3]
            result["summary"] = '. '.join(sentences) + '.'
        
        return result
    
    def _calculate_confidence(self, analysis: Dict[str, Any]) -> float:
        """Calculate confidence score for analysis"""
        
        if "error" in analysis:
            return 0.0
        
        confidence = 0.5  # Base confidence
        
        # Increase confidence based on structured data presence
        if isinstance(analysis, dict):
            if "document_type" in analysis:
                confidence += 0.1
            if "summary" in analysis and len(analysis.get("summary", "")) > 20:
                confidence += 0.1
            if "key_entities" in analysis or "candidate_info" in analysis:
                confidence += 0.1
            
            # Count extracted fields
            field_count = len([k for k, v in analysis.items() if v and k not in ["processing_time_seconds", "model_used", "timestamp", "confidence"]])
            confidence += min(0.2, field_count * 0.02)
        
        return min(1.0, confidence)
    
    def _detect_document_type(self, text: str) -> str:
        """Auto-detect document type from content"""
        
        text_lower = text.lower()
        
        # Check for resume/CV indicators
        resume_indicators = ["resume", "cv", "curriculum vitae", "experience", "education", "skills", "objective"]
        if any(indicator in text_lower for indicator in resume_indicators):
            return "resume"
        
        # Check for contract indicators
        contract_indicators = ["contract", "agreement", "terms and conditions", "whereas", "parties agree"]
        if any(indicator in text_lower for indicator in contract_indicators):
            return "contract"
        
        # Check for invoice indicators  
        invoice_indicators = ["invoice", "bill", "payment due", "total amount", "tax", "subtotal"]
        if any(indicator in text_lower for indicator in invoice_indicators):
            return "invoice"
        
        # Check for report indicators
        report_indicators = ["report", "analysis", "findings", "conclusion", "executive summary"]
        if any(indicator in text_lower for indicator in report_indicators):
            return "report"
        
        return "general"
    
    def _basic_fallback_analysis(self, text: str) -> Dict[str, Any]:
        """Basic fallback analysis without LLM"""
        
        words = text.split()
        
        return {
            "basic_stats": {
                "word_count": len(words),
                "character_count": len(text),
                "paragraph_count": text.count('\n\n') + 1
            },
            "detected_entities": {
                "emails": self._extract_emails(text),
                "phones": self._extract_phones(text), 
                "dates": self._extract_dates(text)
            },
            "summary": text[:200] + "..." if len(text) > 200 else text,
            "analysis_method": "basic_fallback"
        }
    
    def _extract_emails(self, text: str) -> List[str]:
        """Extract email addresses from text"""
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return re.findall(email_pattern, text)
    
    def _extract_phones(self, text: str) -> List[str]:
        """Extract phone numbers from text"""
        import re
        phone_pattern = r'[\+]?[1-9]?[0-9]{7,15}'
        return re.findall(phone_pattern, text)
    
    def _extract_dates(self, text: str) -> List[str]:
        """Extract dates from text"""
        import re
        date_patterns = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{4}',  # MM/DD/YYYY or MM-DD-YYYY
            r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',  # YYYY/MM/DD or YYYY-MM-DD
            r'\d{1,2}/\d{4}',  # MM/YYYY
        ]
        
        dates = []
        for pattern in date_patterns:
            dates.extend(re.findall(pattern, text))
        
        return list(set(dates))  # Remove duplicates