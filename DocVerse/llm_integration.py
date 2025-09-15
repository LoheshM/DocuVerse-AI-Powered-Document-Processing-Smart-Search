import json
import logging
import regex as re
from typing import Dict, Any, Optional
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from config import OPENAI_API_KEY, OPENAI_MODEL, LLM_PROMPT, INTENT_PROMPT, RAG_PROMPT, EMBEDDING_MODEL_NAME
from utils import validate_json_schema, LLM_RESPONSE_SCHEMA, safe_json_parse, normalize_llm_response

logger = logging.getLogger(__name__)

class LLMIntegration:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        # Load the embedding model once
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate a vector embedding for a given text."""
        try:
            # The model expects a list of texts, so we wrap the text in a list
            # and get the first result.
            embedding = self.embedding_model.encode([text])[0]
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None

    def get_intent_and_entities(self, query: str) -> Dict[str, Any]:
        """Parse user query to get filters and semantic query."""
        try:
            prompt = INTENT_PROMPT.format(query=query)
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            parsed_json = safe_json_parse(content)
            return {
                "filters": parsed_json.get("filters", {}),
                "semantic_query": parsed_json.get("semantic_query", query)
            }
        except Exception as e:
            logger.error(f"Error parsing intent: {e}")
            # Fallback if intent parsing fails
            return {"filters": {}, "semantic_query": query}
            
    def generate_rag_response(self, query: str, context: str) -> str:
        """Generate the final answer using the RAG pattern."""
        try:
            prompt = RAG_PROMPT.format(query=query, context=context)
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating RAG response: {e}")
            return "I'm sorry, but I encountered an error while generating the response."


    
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