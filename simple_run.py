#!/usr/bin/env python
"""
Simple script to test running the RAG chatbot pipeline with a PDF file
"""

import os
import sys
import logging
from datetime import datetime
import traceback

# Configure simple logging
logging.basicConfig(level=logging.INFO, 
                   format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

def run_simple_pipeline():
    """Simple function to test running with a PDF"""
    
    print("Starting simple_run.py")
    
    # Path to test_doc.pdf
    pdf_path = os.path.join(os.path.dirname(__file__), "test_doc.pdf")
    print(f"PDF path: {pdf_path}")
    
    # Check if file exists
    if not os.path.exists(pdf_path):
        print(f"Error: File not found at {pdf_path}")
        return
    
    print(f"PDF file exists at: {pdf_path}")
    
    try:
        # Add project root to path to allow imports from src
        sys.path.append(os.path.abspath(os.path.dirname(__file__)))
        print(f"Python path: {sys.path}")
        
        # Import components
        print("Attempting to import components...")
        from src.storage_access import storage
        from src.ingestion_pipeline.ingest import IngestionPipeline
        from src.nlp_llm_pipeline.pipeline import NLPLlmPipeline
        from src.config import LOGGING_CONFIG, API_CONFIG, LLM_CONFIG
        
        print("Successfully imported components")
        print(f"LLM Config: {LLM_CONFIG}")
        
        # Initialize pipeline components
        print("Initializing pipeline components...")
        ingestion_pipeline = IngestionPipeline()
        nlp_pipeline = NLPLlmPipeline()
        print("Pipeline components initialized")
        
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
        print("Step 1: Running ingestion pipeline...")
        document_list = [{
            "url": file_url,
            "doc_type": metadata["doc_type"],
            "file_path": pdf_path  # Pass the file path directly
        }]
        
        # Mock storage functions
        storage_mocked = False
        try:
            storage.connect_to_mongo()
            print("MongoDB connection established")
        except Exception as e:
            print(f"MongoDB connection failed: {e}. Using memory storage.")
            storage_mocked = True
            from unittest.mock import MagicMock
            
            # Create mock methods
            storage.save_document = MagicMock(return_value="dummy-doc-id-123")
            storage.get_document_by_id = MagicMock(return_value={"_id": "dummy-doc-id-123"})
            storage.save_segments = MagicMock()
            storage.get_document_segments = MagicMock(return_value=[{"text": "Segment text from test_doc.pdf."}])
            storage.save_insight = MagicMock()
            storage.query_insights = MagicMock(return_value=[])
        
        ingestion_results = ingestion_pipeline.run(document_list)
        print(f"Ingestion results: {ingestion_results}")
        
        if not ingestion_results or not ingestion_results[0]:
            print("Ingestion pipeline failed")
            return
        
        document_id = ingestion_results[0].get("document_id")
        print(f"Ingestion complete. Document ID: {document_id}")
        
        # Step 2: Get document segments
        print("Step 2: Retrieving document segments...")
        segments = storage.get_document_segments(document_id)
        print(f"Retrieved segments: {segments}")
        
        if not segments:
            print(f"No segments found for document {document_id}")
            return
        
        print(f"Retrieved {len(segments)} document segments")
        
        # Step 3: Run NLP/LLM pipeline
        print("Step 3: Running NLP/LLM pipeline...")
        queries = ["What are the key financial metrics?"]
        
        try:
            # Process document using NLP pipeline
            results = nlp_pipeline.process_document_segments(
                segments=segments,
                document_id=document_id,
                metadata=metadata,
                queries=queries
            )
            
            print("NLP pipeline processing complete")
            
            # Step 4: Display results
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
                
            print("\n=== PROCESSING COMPLETE ===")
        except Exception as e:
            print(f"Error in NLP pipeline: {e}")
            traceback.print_exc()
        
    except Exception as e:
        print(f"Error in pipeline: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    run_simple_pipeline()
