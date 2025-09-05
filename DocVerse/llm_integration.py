import json
import logging
import regex as re
from typing import Dict, Any, Optional
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL, LLM_PROMPT
from utils import validate_json_schema, LLM_RESPONSE_SCHEMA, safe_json_parse, normalize_llm_response

logger = logging.getLogger(__name__)

class LLMIntegration:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
    
    def process_ocr_text(self, ocr_text: str) -> Optional[Dict[str, Any]]:
        """Send OCR text to LLM for processing"""
        try:
            # Prepare the prompt with OCR text (limit length to avoid token limits)
            truncated_ocr = ocr_text[:8000]  # Further reduce to avoid token limits
            prompt = LLM_PROMPT.format(ocr_text=truncated_ocr)
            
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a document processing expert that returns valid JSON. All metadata values must be converted to strings, including numbers."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=4000,
                response_format={"type": "json_object"}
            )
            
            # Extract the response content
            content = response.choices[0].message.content.strip()
            logger.info(f"LLM raw response: {content[:500]}...")  # Log first 500 chars for debugging
            
            # Parse JSON response
            result = safe_json_parse(content)
            
            if result:
                # Normalize the response data types
                normalized_result = normalize_llm_response(result)
                
                # Validate basic structure (skip metadata value type validation)
                if validate_json_schema(normalized_result, LLM_RESPONSE_SCHEMA):
                    logger.info("LLM response validated successfully")
                    return normalized_result
                else:
                    logger.warning("LLM response validation failed, but proceeding with normalized data")
                    return normalized_result
            else:
                logger.error("Failed to parse JSON response from LLM")
                # Try to extract JSON using more aggressive methods
                return self._extract_json_from_text(content)
                
        except Exception as e:
            logger.error(f"LLM processing error: {e}")
            return None
    
    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """Try to extract JSON from LLM response text using multiple methods"""
        try:
            # Method 1: Look for JSON object
            json_match = re.search(r'\{[\s\S]*\}', text)
            if json_match:
                result = json.loads(json_match.group(0))
                return normalize_llm_response(result)
            
            # Method 2: Look for code blocks
            code_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
            if code_match:
                result = json.loads(code_match.group(1))
                return normalize_llm_response(result)
            
            # If all else fails, return a default response
            logger.error("Could not extract JSON from LLM response")
            return {
                "metadata": {},
                "formatted_content": "",
                "formatted_tables": [],
                "entity": "UNKNOWN"
            }
            
        except Exception as e:
            logger.error(f"Error extracting JSON from text: {e}")
            return {
                "metadata": {},
                "formatted_content": "",
                "formatted_tables": [],
                "entity": "UNKNOWN"
            }
    
    def validate_entity(self, entity: str) -> bool:
        """Validate that the entity is in the allowed list"""
        from config import ENTITIES
        return entity in ENTITIES