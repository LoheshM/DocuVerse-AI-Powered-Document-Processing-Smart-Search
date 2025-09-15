import os
import shutil
from datetime import datetime
from typing import Dict, Any, Optional
import logging
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from config import MONGO_URI, DATABASE_NAME, COLLECTION_NAME, BASE_STORAGE_PATH, ENTITIES
from utils import clean_filename, create_directory, get_timestamp
from llm_integration import LLMIntegration

logger = logging.getLogger(__name__)

class StorageManager:
    def __init__(self):
        self.mongo_client = MongoClient(MONGO_URI)
        self.db = self.mongo_client[DATABASE_NAME]
        self.collection = self.db[COLLECTION_NAME]
        self.llm_integration = LLMIntegration() # Initialize for embedding
        
        create_directory(BASE_STORAGE_PATH)

    def resolve_folder_path(self, entity: str) -> Optional[str]:
        """Resolve folder path based on entity type"""
        if entity not in ENTITIES:
            logger.error(f"Unknown entity: {entity}")
            return None
        
        folder_name = ENTITIES[entity]
        folder_path = os.path.join(BASE_STORAGE_PATH, folder_name)
        
        if create_directory(folder_path):
            return folder_path
        return None
    
    def save_to_filesystem(self, file_path: str, entity: str) -> Optional[str]:
        """Save document to appropriate folder based on entity"""
        try:
            folder_path = self.resolve_folder_path(entity)
            if not folder_path:
                return None
            
            # Generate new filename with timestamp
            original_filename = os.path.basename(file_path)
            clean_name = clean_filename(original_filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_filename = f"{clean_name}_{timestamp}{os.path.splitext(original_filename)[1]}"
            destination_path = os.path.join(folder_path, new_filename)
            
            # Copy file to destination
            shutil.copy2(file_path, destination_path)
            
            return destination_path
            
        except Exception as e:
            logger.error(f"Error saving to filesystem: {e}")
            return None
    

    def save_to_mongodb(self, document_data: Dict[str, Any], original_file_path: str) -> bool:
        """Save processed document data and its embedding to MongoDB"""
        try:
            metadata = document_data.get("metadata", {})
            string_metadata = {k: str(v) if v is not None else "" for k, v in metadata.items()}
            
            content_to_embed = document_data.get("formatted_content", "")
            
            # --- NEW: Generate and add embedding ---
            content_embedding = self.llm_integration.generate_embedding(content_to_embed)
            if not content_embedding:
                logger.error(f"Could not generate embedding for {os.path.basename(original_file_path)}")
                # Decide if you want to save without embedding or fail
                # For now, we'll save without it.
                content_embedding = []

            document_record = {
                "filename": os.path.basename(original_file_path),
                "entity": document_data.get("entity", ""),
                "folder_name": ENTITIES.get(document_data.get("entity", ""), ""),
                "metadata": string_metadata,
                "formatted_content": content_to_embed, # Keep original content
                "content_embedding": content_embedding, # <-- NEW FIELD
                "formatted_tables": document_data.get("formatted_tables", []),
                "upload_date": get_timestamp(),
                "storage_path": self.resolve_folder_path(document_data.get("entity", ""))
            }
            
            result = self.collection.insert_one(document_record)
            return result.acknowledged
            
        except PyMongoError as e:
            logger.error(f"MongoDB error: {e}")
            return False
        except Exception as e:
            logger.error(f"Error saving to MongoDB: {e}")
            return False
            
    def process_and_store_document(self, file_path: str, llm_result: Dict[str, Any]) -> bool:
        """Complete document processing and storage"""
        try:
            # Save to filesystem
            fs_path = self.save_to_filesystem(file_path, llm_result.get("entity", ""))
            if not fs_path:
                return False
            
            # Save to MongoDB
            return self.save_to_mongodb(llm_result, file_path)
            
        except Exception as e:
            logger.error(f"Document processing error: {e}")
            return False