#!/usr/bin/env python
"""
Simplified version of run_local_pipeline.py
"""

import os
import sys
import logging
from datetime import datetime
import traceback

# Add project root to path to allow imports from src
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Configure logging
logging.basicConfig(
    filename='simplified_run.log',
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filemode='w'
)

# Also log to console
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger('').addHandler(console)

def run_simplified_pipeline():
    """Runs a simplified version of the RAG pipeline on test_doc.pdf"""
    
    logging.info("Starting simplified pipeline")
    
    # Path to test_doc.pdf
    pdf_path = os.path.join(os.path.dirname(__file__), "test_doc.pdf")
    
    # Check if file exists
    if not os.path.exists(pdf_path):
        logging.error(f"Error: File not found at {pdf_path}")
        return
    
    logging.info(f"PDF file exists at: {pdf_path}")
    
    try:
        # Import components
        logging.info("Importing components...")
        from src.storage_access import storage
        from src.ingestion_pipeline.ingest import IngestionPipeline
        from src.nlp_llm_pipeline.pipeline import NLPLlmPipeline
        from src.config import LOGGING_CONFIG, API_CONFIG, LLM_CONFIG
        
        # Setup mock storage
        logging.info("Setting up mock storage...")
        from unittest.mock import MagicMock
        from bson import ObjectId
        
        # Create mock objects for storage
        mock_documents = {}
        mock_segments = {}
        mock_insights = {}
        
        # Mock storage methods
        def mock_save_document(doc_data):
            doc_id = str(ObjectId())
            mock_documents[doc_id] = doc_data.copy()
            mock_documents[doc_id]['_id'] = doc_id
            return doc_id
            
        def mock_get_document_by_id(doc_id):
            return mock_documents.get(doc_id)
            
        def mock_save_segments(segments, doc_id):
            for segment in segments:
                segment_id = str(ObjectId())
                segment_copy = segment.copy()
                segment_copy['document_id'] = doc_id
                segment_copy['_id'] = segment_id
                mock_segments[segment_id] = segment_copy
                
        def mock_get_document_segments(doc_id):
            return [s for s in mock_segments.values() if s.get('document_id') == doc_id]
            
        def mock_save_insight(data):
            insight_id = str(ObjectId())
            mock_insights[insight_id] = data.copy()
            mock_insights[insight_id]['_id'] = insight_id
            return insight_id
            
        def mock_query_insights(document_id=None, metric=None):
            return [i for i in mock_insights.values() 
                   if (document_id is None or i.get('document_id') == document_id) and
                      (metric is None or i.get('metric_name') == metric)]
        
        # Assign mock methods
        storage.save_document = mock_save_document
        storage.get_document_by_id = mock_get_document_by_id
        storage.save_segments = mock_save_segments
        storage.get_document_segments = mock_get_document_segments
        storage.save_insight = mock_save_insight
        storage.query_insights = mock_query_insights
        
        logging.info("Mock storage set up successfully")
        
        # Initialize pipeline components
        logging.info("Initializing pipeline components...")
        try:
            ingestion_pipeline = IngestionPipeline()
            logging.info("Ingestion pipeline initialized")
        except Exception as e:
            logging.error(f"Error initializing ingestion pipeline: {e}")
            traceback.print_exc()
            return
            
        try:
            nlp_pipeline = NLPLlmPipeline()
            logging.info("NLP pipeline initialized")
        except Exception as e:
            logging.error(f"Error initializing NLP pipeline: {e}")
            traceback.print_exc()
            return
        
        # Create document metadata
        metadata = {
            "company": "Example Corp",
            "doc_type": "Financial Report",
            "original_filename": "test_doc.pdf",
            "upload_timestamp": datetime.now().isoformat()
        }
        
        # Use a file:// URL for local files
        file_url = f"file://{pdf_path}"
        
        # Step 1: Run ingestion pipeline
        logging.info("Step 1: Running ingestion pipeline...")
        try:
            document_list = [{
                "url": file_url,
                "doc_type": metadata["doc_type"],
                "file_path": pdf_path  # Pass the file path directly
            }]
            ingestion_results = ingestion_pipeline.run(document_list)
            
            if not ingestion_results or not ingestion_results[0]:
                logging.error("Ingestion pipeline failed")
                return
            
            document_id = ingestion_results[0].get("document_id")
            logging.info(f"Ingestion complete. Document ID: {document_id}")
        except Exception as e:
            logging.error(f"Error in ingestion pipeline: {e}")
            traceback.print_exc()
            return
        
        # Step 2: Get document segments and process with NLP pipeline
        logging.info("Step 2: Processing document segments...")
        try:
            segments = storage.get_document_segments(document_id)
            
            if not segments:
                logging.error(f"No segments found for document {document_id}")
                return
                
            logging.info(f"Retrieved {len(segments)} document segments")
            
            # Process document using NLP pipeline
            queries = ["What are the key financial metrics?"]
            
            results = nlp_pipeline.process_document_segments(
                segments=segments,
                document_id=document_id,
                metadata=metadata,
                queries=queries
            )
            
            logging.info("Document processing complete")
            logging.info(f"Results: {results}")
            
        except Exception as e:
            logging.error(f"Error processing document: {e}")
            traceback.print_exc()
        
        logging.info("Pipeline execution completed")
        return document_id
        
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    run_simplified_pipeline()
