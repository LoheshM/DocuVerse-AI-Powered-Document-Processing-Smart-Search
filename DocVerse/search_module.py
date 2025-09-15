# search_module.py
from typing import List, Dict, Any, Optional
import logging
import json
from pymongo import MongoClient
from config import MONGO_URI, DATABASE_NAME, COLLECTION_NAME
from llm_integration import LLMIntegration

logger = logging.getLogger(__name__)

class SearchModule:
    def __init__(self):
        self.mongo_client = MongoClient(MONGO_URI)
        self.db = self.mongo_client[DATABASE_NAME]
        self.collection = self.db[COLLECTION_NAME]
        self.llm = LLMIntegration()

    def _build_metadata_query(self, filters: Dict[str, str]) -> Dict[str, Any]:
        """Builds a MongoDB query from a dictionary of filters."""
        if not filters:
            return {}
        query = {"$and": []}
        for field, value in filters.items():
            # Using regex for flexible, case-insensitive matching
            query["$and"].append({f"metadata.{field}": {"$regex": value, "$options": "i"}})
        return query

    def _perform_vector_search(self, query_embedding: List[float], metadata_query: Dict) -> List[Dict]:
        """Performs a vector search on documents matching the metadata query."""
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "vector_index", # The name of your Atlas Search Index
                    "path": "content_embedding",
                    "queryVector": query_embedding,
                    "numCandidates": 100,
                    "limit": 5,
                    "filter": metadata_query
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "filename": 1,
                    "entity": 1,
                    "metadata": 1,
                    "formatted_content": 1,
                    "score": {"$meta": "vectorSearchScore"}
                }
            }
        ]
        try:
            results = list(self.collection.aggregate(pipeline))
            return results
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []
            
    def hybrid_search(self, query: str) -> Dict[str, Any]:
        """Orchestrates the full hybrid search and RAG process."""
        # 1. Parse user query for intent and filters
        intent = self.llm.get_intent_and_entities(query)
        filters = intent.get("filters", {})
        semantic_query = intent.get("semantic_query", query)
        
        logger.info(f"Parsed Intent: Filters={filters}, Semantic Query='{semantic_query}'")
        
        # 2. Build metadata query
        metadata_query = self._build_metadata_query(filters)
        
        # 3. Generate embedding for the semantic query
        query_embedding = self.llm.generate_embedding(semantic_query)
        if not query_embedding:
            return {"answer": "Could not process the query to generate an embedding."}
            
        # 4. Perform vector search with metadata pre-filtering
        search_results = self._perform_vector_search(query_embedding, metadata_query)
        
        if not search_results:
            return {"answer": "I could not find any relevant documents matching your criteria."}
            
        # 5. Build context for RAG
        context = ""
        for res in search_results:
            context += f"Document: {res.get('filename', 'N/A')}\n"
            context += f"Metadata: {json.dumps(res.get('metadata', {}))}\n"
            context += f"Content: {res.get('formatted_content', '')[:1500]}\n---\n" # Truncate content
        
        # 6. Generate final response
        final_answer = self.llm.generate_rag_response(query, context)
        
        return {"answer": final_answer, "sources": search_results}