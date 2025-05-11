#!/usr/bin/env python
# run_local_pipeline.py
"""
End-to-end script to run the RAG chatbot pipeline locally with test_doc.pdf.
This script bypasses the API and directly calls the pipeline components.
"""

import os
import sys
import logging
from datetime import datetime

# Add project root to path to allow imports from src
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Import components
from src.storage_access import storage
from src.ingestion_pipeline.ingest import IngestionPipeline
from src.nlp_llm_pipeline.pipeline import NLPLlmPipeline
from src.config import LOGGING_CONFIG, API_CONFIG, MONGO_CONFIG

# Configure logging
logging.basicConfig(level=getattr(logging, LOGGING_CONFIG["level"]), 
                   format=LOGGING_CONFIG["format"])

def run_local_pipeline():
    """Run the entire RAG pipeline locally on a specified PDF file"""
    
    print("Starting run_local_pipeline function")
    
    # Parse command-line argument for PDF path
    import argparse
    parser = argparse.ArgumentParser(description="Run the RAG pipeline locally on a specified PDF file")
    parser.add_argument("--pdf", type=str, default=os.path.join(os.path.dirname(__file__), "test_doc.pdf"),
                        help="Path to the PDF file to process (defaults to test_doc.pdf)")
    args = parser.parse_args()
    pdf_path = args.pdf
    print(f"Using PDF path: {pdf_path}")
    
    # Check if file exists
    if not os.path.exists(pdf_path):
        logging.error(f"Error: File not found at {pdf_path}")
        print(f"Error: File not found at {pdf_path}")
        return
    
    logging.info(f"Processing file: {pdf_path}")
    print(f"Processing file: {pdf_path}")
    try:
        # Try connecting to MongoDB or use a fallback
        try:
            print("Trying to connect to MongoDB...")
            storage.connect_to_mongo()
            logging.info("MongoDB connection established")
            print("MongoDB connection established")
        except Exception as e:
            logging.warning(f"MongoDB connection failed: {e}. Will use memory storage.")
            print(f"MongoDB connection failed: {e}. Will use memory storage.")
            # Mock storage functions if MongoDB unavailable
            from unittest.mock import MagicMock
            from bson import ObjectId
            
            # Create mock objects for storage
            mock_documents = {}
            mock_segments = {}
            mock_insights = {}
            
            # Override storage functions
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
        
        # Initialize pipeline components
        ingestion_pipeline = IngestionPipeline()
        nlp_pipeline = NLPLlmPipeline()
        
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
        
        # Step 2: Get document segments
        logging.info("Step 2: Retrieving document segments...")
        segments = storage.get_document_segments(document_id)
        
        if not segments:
            logging.error(f"No segments found for document {document_id}")
            return
        
        logging.info(f"Retrieved {len(segments)} document segments")
        
        # Step 3: Run NLP/LLM pipeline
        logging.info("Step 3: Running NLP/LLM pipeline...")
        queries = ["What are the key financial metrics?", "What are the main business risks?"]
        
        # Process document using NLP pipeline
        results = nlp_pipeline.process_document_segments(
            segments=segments,
            document_id=document_id,
            metadata=metadata,
            queries=queries
        )
        
        # Step 4: Display results
        logging.info("Step 4: Processing complete. Results:")
        print("\n=== RAG CHATBOT RESULTS ===")
        
        if results:
            for key, value in results.items():
                print(f"\n== {key} ==")
                if isinstance(value, list):
                    for item in value:
                        print(f"- {item}")
                elif isinstance(value, dict):
                    for k, v in value.items():
                        print(f"- {k}: {v}")
                else:
                    print(value)
        else:
            print("No results generated")
            
        # Step 5: Query some insights
        print("\n=== STORED INSIGHTS ===")
        insights = storage.query_insights(document_id=document_id)
        for insight in insights:
            print(f"- {insight.get('metric_name', 'Unknown')}: {insight.get('value', 'N/A')}")
        
        print("\n=== PROCESSING COMPLETE ===")
        
    except Exception as e:
        logging.error(f"Error in pipeline: {e}", exc_info=True)
    finally:
        # Clean up if needed
        logging.info("Pipeline execution completed")

if __name__ == "__main__":
    run_local_pipeline()
