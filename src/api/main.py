from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
import os
import sys
import tempfile
import shutil
import logging
from datetime import datetime
import json

# Add project root to path to allow imports from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.storage_access import storage
from src.monitoring_feedback import logger
from src.ingestion_pipeline.ingest import IngestionPipeline
from src.nlp_llm_pipeline.pipeline import NLPLlmPipeline
from src.config import LOGGING_CONFIG, API_CONFIG
from src.document_processor.processor import load_document

# Configure logging
logging.basicConfig(level=getattr(logging, LOGGING_CONFIG["level"]), 
                   format=LOGGING_CONFIG["format"])

app = FastAPI(
    title="Financial Document Intelligence System",
    description="API for financial document analysis and insight extraction",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=API_CONFIG["cors_origins"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize pipeline components
ingestion_pipeline = IngestionPipeline()
nlp_pipeline = NLPLlmPipeline()

# Create a dependency for authentication (to be implemented in production)
async def verify_api_key(api_key: str = Query(..., description="API key for authentication")):
    """
    A simple API key verification dependency.
    In production, this should be replaced with a more robust solution.
    """
    if api_key != API_CONFIG["api_key"]:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "online", 
        "service": "Financial Document Intelligence System API",
        "version": "1.0.0"
    }

@app.post("/upload-document/")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    doc_type: str = Query(..., description="Document type (e.g., 10-K, 10-Q, earnings_call)"),
    company: str = Query(None, description="Company name"),
    api_key: str = Depends(verify_api_key)
):
    """
    Upload a financial document for processing and insight extraction.
    
    The document will be processed in the background, and insights will be extracted.
    """
    # Create a temporary file to save the uploaded document
    try:
        # Create temp file with the same suffix as the original file
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_file_path = temp_file.name
            
        logging.info(f"Document saved temporarily to {temp_file_path}")
        
        # Metadata for document processing
        metadata = {
            "company": company or "Unknown",
            "doc_type": doc_type,
            "original_filename": file.filename,
            "upload_timestamp": datetime.now().isoformat(),
            "file_path": temp_file_path
        }
        
        # Add document processing to background tasks
        background_tasks.add_task(
            process_document_background, 
            temp_file_path, 
            doc_type,
            metadata
        )
        
        return {
            "filename": file.filename,
            "document_type": doc_type,
            "company": metadata["company"],
            "message": "Document uploaded and processing initiated in the background.",
        }
        
    except Exception as e:
        logging.error(f"Error processing document upload: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")
    finally:
        # Close the file
        file.file.close()

@app.post("/analyze-document/{document_id}")
async def analyze_document(
    document_id: int,
    background_tasks: BackgroundTasks,
    queries: List[str] = Query(None, description="Specific queries or metrics to extract"),
    api_key: str = Depends(verify_api_key)
):
    """
    Analyze a previously uploaded document by ID.
    
    This endpoint will trigger the NLP pipeline to analyze the document and extract insights.
    """
    # Check if document exists
    document = storage.get_document_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail=f"Document with ID {document_id} not found")
        
    # Get document segments
    segments = storage.get_document_segments(document_id)
    if not segments:
        raise HTTPException(status_code=404, detail=f"No segments found for document {document_id}")
        
    # Add analysis task to background tasks
    background_tasks.add_task(
        analyze_document_background,
        document_id,
        document,
        segments,
        queries
    )
    
    return {
        "document_id": document_id,
        "message": "Document analysis initiated in the background.",
        "company": document.get("company", "Unknown"),
        "document_type": document.get("doc_type", "Unknown")
    }

@app.post("/analyze-example-text/")
async def analyze_example_text(
    background_tasks: BackgroundTasks,
    doc_type: str = Query("financial_report", description="Document type (e.g., 10-K, 10-Q, earnings_call)"),
    company: str = Query("Example Corp", description="Company name"),
    queries: List[str] = Query(None, description="Specific queries or metrics to extract"),
    api_key: str = Depends(verify_api_key)
):
    """
    Analyze the example financial text directly without requiring file upload.
    
    This endpoint uses the example_financial_text.txt file directly.
    """
    try:
        # Create metadata for document processing
        metadata = {
            "company": company,
            "doc_type": doc_type,
            "original_filename": "example_financial_text.txt",
            "upload_timestamp": datetime.now().isoformat(),
            "file_path": "#file:example_financial_text.txt"  # Special identifier
        }
        
        # Process document
        document_result = process_local_document("#file:example_financial_text.txt", doc_type, metadata)
        
        if not document_result["success"]:
            raise HTTPException(status_code=500, detail=f"Error processing example text: {document_result.get('error', 'Unknown error')}")
            
        document_id = document_result["document_id"]
        
        # Add analysis task to background tasks
        background_tasks.add_task(
            analyze_document_background,
            document_id,
            document_result["metadata"],
            document_result["segments"],
            queries
        )
        
        return {
            "document_id": document_id,
            "message": "Example text analysis initiated in the background.",
            "company": company,
            "document_type": doc_type
        }
        
    except Exception as e:
        logging.error(f"Error processing example text: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing example text: {str(e)}")

@app.get("/insights/")
async def get_all_insights(
    limit: int = Query(100, description="Maximum number of insights to return"),
    offset: int = Query(0, description="Number of insights to skip"),
    api_key: str = Depends(verify_api_key)
):
    """
    Retrieve all extracted financial insights with pagination.
    """
    insights = storage.get_all_insights()
    
    # Apply pagination
    paginated_insights = insights[offset:offset + limit] if insights else []
    
    # Convert the list of tuples to a list of dictionaries for better JSON representation
    insight_list = []
    for insight in paginated_insights:
        insight_list.append({
            "id": insight[0],
            "metric": insight[1],
            "value": insight[2],
            "timestamp": insight[3],
            "company": insight[4],
            "source_reference": insight[5],
            "model_version": insight[6],
            "original_text": insight[7],
            "page_numbers": insight[8]
        })
    
    return {
        "insights": insight_list,
        "total": len(insights),
        "limit": limit,
        "offset": offset
    }

@app.get("/insights/query/")
async def query_insights(
    metric: Optional[str] = None,
    date: Optional[str] = None,
    company: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
):
    """
    Query financial insights based on metric, date, and company.
    """
    insights = storage.query_insights(metric=metric, date=date, company=company)
    
    # Convert the list of tuples to a list of dictionaries for better JSON representation
    insight_list = []
    for insight in insights:
        insight_list.append({
            "id": insight[0],
            "metric": insight[1],
            "value": insight[2],
            "timestamp": insight[3],
            "company": insight[4],
            "source_reference": insight[5],
            "model_version": insight[6],
            "original_text": insight[7],
            "page_numbers": insight[8]
        })
    
    return insight_list

@app.get("/documents/")
async def get_all_documents(
    limit: int = Query(100, description="Maximum number of documents to return"),
    offset: int = Query(0, description="Number of documents to skip"),
    api_key: str = Depends(verify_api_key)
):
    """
    Retrieve all processed documents with pagination.
    """
    # This function needs to be implemented in the storage module
    documents = storage.get_all_documents() if hasattr(storage, 'get_all_documents') else []
    
    # Apply pagination
    paginated_documents = documents[offset:offset + limit] if documents else []
    
    return {
        "documents": paginated_documents,
        "total": len(documents),
        "limit": limit,
        "offset": offset
    }

@app.get("/documents/{document_id}")
async def get_document(
    document_id: int,
    api_key: str = Depends(verify_api_key)
):
    """
    Retrieve a specific document by ID.
    """
    document = storage.get_document_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail=f"Document with ID {document_id} not found")
        
    # Get document segments
    segments = storage.get_document_segments(document_id)
    
    # Get insights related to this document
    insights = storage.get_insights_by_document(document_id)
    
    # Convert insights to a list of dictionaries
    insight_list = []
    for insight in insights:
        insight_list.append({
            "id": insight[0],
            "metric": insight[1],
            "value": insight[2],
            "timestamp": insight[3],
            "company": insight[4],
            "source_reference": insight[5],
            "model_version": insight[6],
            "original_text": insight[7],
            "page_numbers": insight[8]
        })
    
    # Return document with segments and insights
    return {
        "document": document,
        "segments": segments,
        "insights": insight_list
    }

@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify system components.
    """
    health_status = {
        "api": "healthy",
        "database": "unknown",
        "ingestion_pipeline": "healthy",
        "nlp_pipeline": "healthy"
    }
    
    # Check database connection
    try:
        # Try to execute a simple query
        storage.get_all_insights()
        health_status["database"] = "healthy"
    except Exception as e:
        health_status["database"] = f"unhealthy: {str(e)}"
        
    return health_status

# Background processing functions
async def process_document_background(file_path, doc_type, metadata):
    """
    Process an uploaded document in the background.
    
    Args:
        file_path: Path to the temporary file
        doc_type: Type of document (10-K, 10-Q, etc.)
        metadata: Additional metadata about the document
    """
    logging.info(f"Starting background processing of document: {metadata.get('original_filename')}")
    try:
        # In a real scenario, the document would come from a URL
        # Here, we modify the ingest pipeline to work with local files
        document_result = process_local_document(file_path, doc_type, metadata)
        
        if document_result["success"] and document_result["document_id"]:
            document_id = document_result["document_id"]
            segments = document_result["segments"]
            
            # Now run the NLP pipeline on the document
            logging.info(f"Starting NLP processing for document ID: {document_id}")
            
            # Process document segments with NLP pipeline
            analyze_document_background(document_id, document_result["metadata"], segments)
            
            logging.info(f"Background processing complete for document ID: {document_id}")
        else:
            logging.error(f"Document processing failed: {document_result.get('error', 'Unknown error')}")
    except Exception as e:
        logging.error(f"Error in background document processing: {e}")
    finally:
        # Clean up temp file if it still exists
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logging.info(f"Temporary file removed: {file_path}")
            except Exception as e:
                logging.error(f"Failed to remove temporary file: {e}")

def process_local_document(file_path, doc_type, metadata):
    """
    Process a local document file that has been uploaded.
    
    Args:
        file_path: Path to the document file
        doc_type: Type of document
        metadata: Additional metadata
    
    Returns:
        dict: Result of document processing
    """
    try:
        logging.info(f"Processing local document: {file_path}")
        
        # Get the document text using our processor
        document_text = load_document(file_path)
        
        # Save document metadata in database
        document_data = {
            'company': metadata.get('company', 'Unknown'),
            'doc_type': doc_type,
            'filing_date': datetime.now(),
            'source_url': metadata.get('source_url', None),
            'file_path': file_path,
            'processed': False  # Will be marked as processed after NLP pipeline
        }
        
        document_id = storage.save_document(document_data)
        if not document_id:
            return {"success": False, "error": "Failed to save document metadata"}
            
        # Create basic segments (for now just one segment with all text)
        segments = [{
            'section_type': 'Full Document',
            'text': document_text,
            'start_page': 0,
            'end_page': 0
        }]
        
        # Save segments
        storage.save_segments(segments, document_id)
        
        # Return the document ID and segments for further processing
        return {
            "success": True, 
            "document_id": document_id, 
            "segments": segments,
            "metadata": document_data
        }
        
    except Exception as e:
        logging.error(f"Error processing local document: {e}")
        return {"success": False, "error": str(e)}

async def analyze_document_background(document_id, document, segments, queries=None):
    """
    Run NLP analysis on a document in the background.
    
    Args:
        document_id: ID of the document to analyze
        document: Document metadata
        segments: Document segments
        queries: Optional specific metrics to extract
    """
    logging.info(f"Starting NLP analysis for document ID: {document_id}")
    try:
        # Extract text from segments
        segment_texts = [segment["text"] for segment in segments]
        
        # Combine for full document text
        full_document_text = "\n\n".join(segment_texts)
        
        # Process with NLP pipeline
        metadata = {
            "company": document.get("company", "Unknown"),
            "filing_date": document.get("filing_date"),
            "doc_type": document.get("doc_type")
        }
        
        # Process document with NLP pipeline
        insights = nlp_pipeline.process_document(
            document_text=full_document_text,
            document_id=document_id,
            metadata=metadata,
            queries=queries
        )
        
        # Save extracted insights to database
        save_insights_to_database(document_id, insights)
        
        # Log the prediction
        logger.log_prediction(str(document_id), insights)
        
        logging.info(f"NLP processing complete for document ID: {document_id}")
    except Exception as e:
        logging.error(f"Error in NLP document analysis: {e}")

def save_insights_to_database(document_id, insights):
    """
    Save extracted insights to the database.
    
    Args:
        document_id: ID of the document
        insights: Dictionary of extracted insights
    """
    try:
        # Save metrics
        for metric_name, metric_value in insights.get("extracted_metrics", {}).items():
            insight_data = {
                "metric": metric_name,
                "value": metric_value,
                "timestamp": insights.get("timestamp"),
                "company": insights.get("company", "Unknown"),
                "source_reference": f"document_id={document_id}, type=metric",
                "model_version": insights.get("model_version"),
                "original_text": "", # This should ideally be the specific text that led to this insight
                "page_numbers": []   # This should ideally be the page numbers where this insight was found
            }
            storage.save_insight(insight_data)
            
        # Save sentiment analysis
        if "sentiment" in insights:
            insight_data = {
                "metric": "sentiment",
                "value": insights["sentiment"],
                "timestamp": insights.get("timestamp"),
                "company": insights.get("company", "Unknown"),
                "source_reference": f"document_id={document_id}, type=sentiment",
                "model_version": insights.get("model_version"),
                "original_text": "",
                "page_numbers": []
            }
            storage.save_insight(insight_data)
            
        # Save risk identification
        if "risks" in insights:
            insight_data = {
                "metric": "risks",
                "value": insights["risks"],
                "timestamp": insights.get("timestamp"),
                "company": insights.get("company", "Unknown"),
                "source_reference": f"document_id={document_id}, type=risks",
                "model_version": insights.get("model_version"),
                "original_text": "",
                "page_numbers": []
            }
            storage.save_insight(insight_data)
            
        # Save summary
        if "summary" in insights:
            insight_data = {
                "metric": "summary",
                "value": insights["summary"],
                "timestamp": insights.get("timestamp"),
                "company": insights.get("company", "Unknown"),
                "source_reference": f"document_id={document_id}, type=summary",
                "model_version": insights.get("model_version"),
                "original_text": "",
                "page_numbers": []
            }
            storage.save_insight(insight_data)
            
        logging.info(f"Saved insights for document ID: {document_id}")
    except Exception as e:
        logging.error(f"Error saving insights to database: {e}")

if __name__ == "__main__":
    import uvicorn
    # Initialize database
    storage.initialize_database()
    # Start the FastAPI server
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)