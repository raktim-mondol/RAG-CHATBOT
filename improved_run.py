#!/usr/bin/env python
"""
Improved script to test running the RAG chatbot pipeline with a PDF file
"""

import os
import sys
import logging
from datetime import datetime
import traceback

# Configure logging to file
logging.basicConfig(
    filename='rag_run.log',
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filemode='w'  # Overwrite existing log file
)

# Also log to console
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger('').addHandler(console)

logger = logging.getLogger(__name__)

def run_improved_pipeline():
    """Improved function to test running with a PDF"""
    
    logger.info("Starting improved_run.py")
    
    # Path to test_doc.pdf
    pdf_path = os.path.join(os.path.dirname(__file__), "test_doc.pdf")
    logger.info(f"PDF path: {pdf_path}")
    
    # Check if file exists
    if not os.path.exists(pdf_path):
        logger.error(f"Error: File not found at {pdf_path}")
        return
    
    logger.info(f"PDF file exists at: {pdf_path}")
    
    try:
        # Add project root to path to allow imports from src
        sys.path.append(os.path.abspath(os.path.dirname(__file__)))
        logger.info(f"Python path: {sys.path}")
        
        # Import components
        logger.info("Attempting to import components...")
        try:
            from src.storage_access import storage
            from src.ingestion_pipeline.ingest import IngestionPipeline
            from src.nlp_llm_pipeline.pipeline import NLPLlmPipeline
            from src.config import LOGGING_CONFIG, API_CONFIG, LLM_CONFIG
            
            logger.info("Successfully imported components")
            logger.info(f"LLM Config: {LLM_CONFIG}")
        except Exception as e:
            logger.error(f"Error importing components: {e}")
            traceback.print_exc()
            return
        
        # Initialize pipeline components
        try:
            logger.info("Initializing pipeline components...")
            ingestion_pipeline = IngestionPipeline()
            nlp_pipeline = NLPLlmPipeline()
            logger.info("Pipeline components initialized")
        except Exception as e:
            logger.error(f"Error initializing pipeline components: {e}")
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
        
        # Set up mock storage if needed
        try:
            logger.info("Setting up storage...")
            try:
                storage.connect_to_mongo()
                logger.info("MongoDB connection established")
            except Exception as e:
                logger.warning(f"MongoDB connection failed: {e}. Using memory storage.")
                
                # Create mock storage
                from unittest.mock import MagicMock
                from bson import ObjectId
                
                # Create mock objects for storage
                mock_documents = {}
                mock_segments = {}
                mock_insights = {}
                
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
                
                logger.info("Mock storage functions configured")
        except Exception as e:
            logger.error(f"Error setting up storage: {e}")
            traceback.print_exc()
            return
        
        # Step 1: Run ingestion pipeline
        try:
            logger.info("Step 1: Running ingestion pipeline...")
            document_list = [{
                "url": file_url,
                "doc_type": metadata["doc_type"],
                "file_path": pdf_path  # Pass the file path directly
            }]
            
            ingestion_results = ingestion_pipeline.run(document_list)
            logger.info(f"Ingestion results: {ingestion_results}")
            
            if not ingestion_results or not ingestion_results[0]:
                logger.error("Ingestion pipeline failed")
                return
            
            document_id = ingestion_results[0].get("document_id")
            logger.info(f"Ingestion complete. Document ID: {document_id}")
        except Exception as e:
            logger.error(f"Error in ingestion pipeline: {e}")
            traceback.print_exc()
            return
        
        # Step 2: Get document segments
        try:
            logger.info("Step 2: Retrieving document segments...")
            segments = storage.get_document_segments(document_id)
            
            if not segments:
                logger.error(f"No segments found for document {document_id}")
                return
            
            logger.info(f"Retrieved {len(segments)} document segments")
        except Exception as e:
            logger.error(f"Error retrieving document segments: {e}")
            traceback.print_exc()
            return
        
        # Step 3: Run NLP/LLM pipeline
        try:
            logger.info("Step 3: Running NLP/LLM pipeline...")
            queries = ["What are the key financial metrics?", "What are the main business risks?"]
            
            # Process document using NLP pipeline
            results = nlp_pipeline.process_document_segments(
                segments=segments,
                document_id=document_id,
                metadata=metadata,
                queries=queries
            )
            
            logger.info("NLP pipeline processing complete")
            
            # Step 4: Display results
            logger.info("\n=== RAG CHATBOT RESULTS ===")
            
            if results:
                for key, value in results.items():
                    logger.info(f"\n== {key} ==")
                    if isinstance(value, list):
                        for item in value:
                            logger.info(f"- {item}")
                    elif isinstance(value, dict):
                        for k, v in value.items():
                            logger.info(f"- {k}: {v}")
                    else:
                        logger.info(value)
            else:
                logger.info("No results generated")
                
            # Step 5: Query some insights
            logger.info("\n=== STORED INSIGHTS ===")
            insights = storage.query_insights(document_id=document_id)
            for insight in insights:
                logger.info(f"- {insight.get('metric_name', 'Unknown')}: {insight.get('value', 'N/A')}")
            
            logger.info("\n=== PROCESSING COMPLETE ===")
        except Exception as e:
            logger.error(f"Error in NLP pipeline: {e}")
            traceback.print_exc()
            
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    run_improved_pipeline()
