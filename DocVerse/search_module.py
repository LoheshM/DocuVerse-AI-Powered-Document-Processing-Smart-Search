from typing import List, Dict, Any
import logging
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from config import MONGO_URI, DATABASE_NAME, COLLECTION_NAME

logger = logging.getLogger(__name__)

class SearchModule:
    def __init__(self):
        self.mongo_client = MongoClient(MONGO_URI)
        self.db = self.mongo_client[DATABASE_NAME]
        self.collection = self.db[COLLECTION_NAME]
    
    def search_by_metadata(self, field: str, value: str, exact_match: bool = True) -> List[Dict[str, Any]]:
        """Search documents by metadata field"""
        try:
            if exact_match:
                query = {f"metadata.{field}": value}
            else:
                query = {f"metadata.{field}": {"$regex": value, "$options": "i"}}
            
            results = self.collection.find(
                query,
                {
                    "filename": 1,
                    "entity": 1,
                    "folder_name": 1,
                    "metadata": 1,
                    "_id": 0
                }
            )
            
            return list(results)
            
        except PyMongoError as e:
            logger.error(f"MongoDB search error: {e}")
            return []
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    def search_multiple_fields(self, criteria: Dict[str, str]) -> List[Dict[str, Any]]:
        """Search using multiple field criteria"""
        try:
            query = {}
            for field, value in criteria.items():
                query[f"metadata.{field}"] = {"$regex": value, "$options": "i"}
            
            results = self.collection.find(
                query,
                {
                    "filename": 1,
                    "entity": 1,
                    "folder_name": 1,
                    "metadata": 1,
                    "_id": 0
                }
            )
            
            return list(results)
            
        except Exception as e:
            logger.error(f"Multi-field search error: {e}")
            return []