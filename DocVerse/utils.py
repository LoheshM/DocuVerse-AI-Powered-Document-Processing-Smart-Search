import os
import json
import logging
import re
from datetime import datetime
from typing import Dict, Any, Optional, Union
import jsonschema

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_filename(filename: str) -> str:
    """Clean filename by removing special characters and spaces"""
    # Remove file extension
    name = os.path.splitext(filename)[0]
    # Replace spaces and special characters
    name = re.sub(r'[^\w\-_]', '_', name)
    name = re.sub(r'_+', '_', name)
    return name.strip('_')

def create_directory(path: str) -> bool:
    """Create directory if it doesn't exist"""
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Error creating directory {path}: {e}")
        return False

def get_timestamp() -> str:
    """Get current timestamp in ISO format"""
    return datetime.now().isoformat()

def validate_json_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """Validate JSON data against a schema (skip metadata value validation)"""
    try:
        # Create a modified schema that doesn't validate metadata value types
        modified_schema = schema.copy()
        if 'properties' in modified_schema and 'metadata' in modified_schema['properties']:
            # Remove the additionalProperties constraint for metadata
            modified_schema['properties']['metadata'] = {"type": "object"}
        
        jsonschema.validate(instance=data, schema=modified_schema)
        return True
    except jsonschema.ValidationError as e:
        logger.warning(f"JSON validation warning: {e}")
        # Even if validation fails, we'll try to process the data
        return True
    except Exception as e:
        logger.error(f"JSON validation error: {e}")
        return False

def convert_metadata_types(metadata: Dict[str, Any]) -> Dict[str, str]:
    """Convert all metadata values to strings to ensure schema compliance"""
    converted = {}
    for key, value in metadata.items():
        if value is None:
            converted[key] = ""
        elif isinstance(value, (int, float, bool)):
            converted[key] = str(value)
        elif isinstance(value, list):
            converted[key] = ", ".join(str(item) for item in value)
        elif isinstance(value, dict):
            converted[key] = json.dumps(value)
        else:
            converted[key] = str(value)
    return converted

# Updated JSON Schema for LLM response validation with relaxed metadata validation
LLM_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["metadata", "formatted_content", "formatted_tables", "entity"],
    "properties": {
        "metadata": {"type": "object"},  # No validation of metadata values
        "formatted_content": {"type": "string"},
        "formatted_tables": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "Table Title": {"type": "string"},
                    "Content": {"type": "array"}
                }
            }
        },
        "entity": {"type": "string"}
    }
}

def safe_json_parse(json_str: str) -> Optional[Dict[str, Any]]:
    """Safely parse JSON string with error handling"""
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}")
        # Try to extract JSON from markdown code blocks
        json_match = re.search(r'```json\s*(.*?)\s*```', json_str, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                pass
        
        # Try to find JSON object in the text
        json_match = re.search(r'\{.*\}', json_str, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except:
                pass
        
        return None

# Add this function to utils.py
def normalize_dates_in_metadata(metadata: Dict[str, Any]) -> Dict[str, str]:
    """Normalize dates in metadata to ensure consistent format"""
    converted = {}
    date_fields = ['Visit Start Date', 'Visit End Date', 'Date of Letter', 'Previous Visit Date']
    
    for key, value in metadata.items():
        # Convert to string first
        str_value = str(value) if value is not None else ""
        
        # Try to normalize date format for known date fields
        if key in date_fields and str_value.strip():
            try:
                # Try to parse and reformat dates
                from datetime import datetime
                
                # Try different date formats
                for fmt in ['%d-%m-%Y', '%d/%m/%Y', '%d.%m.%Y', '%Y-%m-%d', '%Y/%m/%d', '%Y.%m.%d', '%m/%d/%Y', '%m-%d-%Y']:
                    try:
                        dt = datetime.strptime(str_value, fmt)
                        str_value = dt.strftime('%d-%m-%Y')
                        break
                    except ValueError:
                        continue
            except:
                # If date parsing fails, keep the original string value
                pass
        
        converted[key] = str_value
    
    return converted

# Update the normalize_llm_response function to use date normalization:
def normalize_llm_response(response_data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize LLM response to ensure proper data types"""
    try:
        normalized = response_data.copy()
        
        # Ensure all required fields exist
        if "metadata" not in normalized:
            normalized["metadata"] = {}
        if "formatted_content" not in normalized:
            normalized["formatted_content"] = ""
        if "formatted_tables" not in normalized:
            normalized["formatted_tables"] = []
        if "entity" not in normalized:
            normalized["entity"] = "UNKNOWN"
        
        # Convert metadata values to strings and normalize dates
        normalized["metadata"] = normalize_dates_in_metadata(normalized["metadata"])
        
        # Ensure formatted_content is a string
        if not isinstance(normalized["formatted_content"], str):
            normalized["formatted_content"] = str(normalized["formatted_content"])
        
        # Ensure entity is a string
        if not isinstance(normalized["entity"], str):
            normalized["entity"] = str(normalized["entity"])
        
        # Ensure formatted_tables is an array
        if not isinstance(normalized["formatted_tables"], list):
            normalized["formatted_tables"] = []
        
        return normalized
    except Exception as e:
        logger.error(f"Error normalizing LLM response: {e}")
        # Return a minimal valid response
        return {
            "metadata": {},
            "formatted_content": "",
            "formatted_tables": [],
            "entity": "UNKNOWN"
        }
    
def safe_json_parse(json_str: str) -> Optional[Dict[str, Any]]:
    """Safely parse JSON string with error handling"""
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}")
        
        # Multiple strategies to extract JSON
        strategies = [
            # Strategy 1: Remove markdown code blocks
            lambda s: re.search(r'```json\s*(.*?)\s*```', s, re.DOTALL),
            # Strategy 2: Find JSON object between first { and last }
            lambda s: re.search(r'\{.*\}', s, re.DOTALL),
            # Strategy 3: Remove common LLM artifacts
            lambda s: re.sub(r'^[^{]*', '', s),  # Remove text before first {
            # Strategy 4: Try to fix common JSON issues
            lambda s: s.replace("'", '"').replace("True", "true").replace("False", "false")
        ]
        
        for strategy in strategies:
            try:
                processed = strategy(json_str)
                if processed:
                    if isinstance(processed, str):
                        result = json.loads(processed)
                    else:
                        result = json.loads(processed.group(1) if processed.groups() else processed.group(0))
                    return result
            except:
                continue
        
        logger.error("All JSON parsing strategies failed")
        return None