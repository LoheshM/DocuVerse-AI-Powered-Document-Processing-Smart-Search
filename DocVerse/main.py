import os
import logging
import argparse
from typing import List, Dict, Any
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

from ocr_processor import OCRProcessor
from llm_integration import LLMIntegration
from storage_manager import StorageManager
from search_module import SearchModule
from utils import create_directory, get_timestamp
from config import TEMP_UPLOAD_DIR

# Initialize components
app = FastAPI(title="Document Processing System")
ocr_processor = OCRProcessor()
llm_integration = LLMIntegration()
storage_manager = StorageManager()
search_module = SearchModule()

# Create temp directory
create_directory(TEMP_UPLOAD_DIR)

# In the process_single_document function, add more logging:
def process_single_document(file_path: str) -> Dict[str, Any]:
    """Process a single document through the entire pipeline"""
    try:
        # Step 1: OCR Processing
        logging.info(f"Processing document: {file_path}")
        ocr_text = ocr_processor.process_document(file_path)
        print(ocr_text)
        if not ocr_text:
            raise Exception("OCR processing failed - no text extracted")
        
        logging.info(f"OCR extracted {len(ocr_text)} characters")
        logging.debug(f"First 500 chars: {ocr_text[:500]}")
        
        # Step 2: LLM Processing
        llm_result = llm_integration.process_ocr_text(ocr_text)
        
        if not llm_result:
            raise Exception("LLM processing failed - no result returned")
        
        # Validate entity
        entity = llm_result.get("entity", "")
        if not llm_integration.validate_entity(entity):
            raise Exception(f"Invalid entity: {entity}")
        
        logging.info(f"LLM processing successful. Entity: {entity}")
        logging.info(f"Extracted {len(llm_result.get('metadata', {}))} metadata fields")
        
        # Step 3: Storage
        if not storage_manager.process_and_store_document(file_path, llm_result):
            raise Exception("Storage failed")
        
        return {
            "status": "success",
            "filename": os.path.basename(file_path),
            "entity": entity,
            "processing_time": get_timestamp(),
            "metadata_fields": len(llm_result.get("metadata", {})),
            "llm_response": llm_result  # Add this line to include the full LLM response
        }
        
    except Exception as e:
        logging.error(f"Document processing error: {e}")
        return {
            "status": "error",
            "filename": os.path.basename(file_path),
            "error": str(e),
            "processing_time": get_timestamp()
        }
            
@app.post("/upload/")
async def upload_documents(files: List[UploadFile] = File(...)):
    """API endpoint for document upload"""
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")
    
    results = []
    
    for file in files:
        try:
            # Save uploaded file temporarily
            temp_path = os.path.join(TEMP_UPLOAD_DIR, file.filename)
            with open(temp_path, "wb") as f:
                content = await file.read()
                f.write(content)
            
            # Process document
            result = process_single_document(temp_path)
            results.append(result)
            
            # Clean up temp file
            try:
                os.remove(temp_path)
            except:
                pass
            
        except Exception as e:
            results.append({
                "status": "error",
                "filename": file.filename,
                "error": str(e)
            })
    
    return JSONResponse(content={"results": results})

@app.get("/search/")
async def search_documents(field: str, value: str, exact: bool = True):
    """API endpoint for metadata search"""
    try:
        results = search_module.search_by_metadata(field, value, exact)
        return JSONResponse(content={"results": results})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": get_timestamp()}

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Document Processing System API", "status": "running"}

def cli_interface():
    """Command-line interface"""
    parser = argparse.ArgumentParser(description="Document Processing System")
    parser.add_argument("files", nargs="*", help="Files to process")
    parser.add_argument("--search", nargs=2, metavar=("FIELD", "VALUE"), 
                       help="Search for documents by metadata field")
    
    args = parser.parse_args()
    
    if args.search:
        # Search mode
        field, value = args.search
        results = search_module.search_by_metadata(field, value, True)
        for result in results:
            print(f"File: {result['filename']}")
            print(f"Entity: {result['entity']}")
            print(f"Folder: {result['folder_name']}")
            print("---")
    elif args.files:
        # Processing mode
        for file_path in args.files:
            if os.path.exists(file_path):
                result = process_single_document(file_path)
                print(f"Processed {file_path}: {result['status']}")
                if result['status'] == 'success':
                    print(f"  Entity: {result['entity']}")
            else:
                print(f"File not found: {file_path}")
    else:
        # Start web server if no arguments
        print("Starting Document Processing System API server...")
        print("API available at: http://localhost:8000")
        print("Use --help for CLI usage")
        uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    cli_interface()