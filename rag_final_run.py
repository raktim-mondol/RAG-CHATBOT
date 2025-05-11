#!/usr/bin/env python
"""
Final RAG chatbot script for running end-to-end with test_doc.pdf
"""

import os
import sys
import logging
from datetime import datetime
import traceback

# Add project root to path to allow imports from src
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Configure logging to be simple and write to a file
with open("rag_final_run.txt", "w", encoding="utf-8") as log_file:
    log_file.write(f"RAG Chatbot Run - {datetime.now()}\n\n")
    
    try:
        log_file.write("1. Setting up environment and imports...\n")
        # Import necessary components
        from src.storage_access import storage
        from src.ingestion_pipeline.ingest import IngestionPipeline
        from src.nlp_llm_pipeline.pipeline import NLPLlmPipeline
        from src.config import LLM_CONFIG
        log_file.write("   Imports successful\n")
        
        # Setup mock storage (in-memory)
        log_file.write("2. Setting up mock storage...\n")
        from unittest.mock import MagicMock
        from bson import ObjectId
        
        # Create mock objects for storage
        mock_documents = {}
        mock_segments = {}
        mock_insights = {}
        
        # Define mock methods
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
        log_file.write("   Mock storage setup complete\n")
        
        # Check for test_doc.pdf
        log_file.write("3. Checking for test_doc.pdf...\n")
        pdf_path = os.path.join(os.path.dirname(__file__), "test_doc.pdf")
        if not os.path.exists(pdf_path):
            log_file.write(f"   Error: File not found at: {pdf_path}\n")
            sys.exit(1)
        log_file.write(f"   Found PDF file at: {pdf_path}\n")
        
        # Initialize pipeline components
        log_file.write("4. Initializing pipeline components...\n")
        ingestion_pipeline = IngestionPipeline()
        log_file.write("   Ingestion pipeline initialized\n")
        
        nlp_pipeline = NLPLlmPipeline()
        log_file.write("   NLP pipeline initialized\n")
        
        # Create document metadata
        metadata = {
            "company": "Example Corp",
            "doc_type": "Financial Report",
            "original_filename": "test_doc.pdf",
            "upload_timestamp": datetime.now().isoformat()
        }
        
        # Run ingestion pipeline
        log_file.write("5. Running ingestion pipeline...\n")
        file_url = f"file://{pdf_path}"
        document_list = [{
            "url": file_url,
            "doc_type": metadata["doc_type"],
            "file_path": pdf_path
        }]
        
        ingestion_results = ingestion_pipeline.run(document_list)
        if not ingestion_results or not ingestion_results[0]:
            log_file.write("   Ingestion pipeline failed\n")
            sys.exit(1)
        
        document_id = ingestion_results[0].get("document_id")
        log_file.write(f"   Ingestion complete. Document ID: {document_id}\n")
        
        # Get document segments
        log_file.write("6. Retrieving document segments...\n")
        segments = storage.get_document_segments(document_id)
        if not segments:
            log_file.write(f"   No segments found for document {document_id}\n")
            sys.exit(1)
        log_file.write(f"   Retrieved {len(segments)} document segments\n")
        
        # Process with NLP pipeline
        log_file.write("7. Running NLP/LLM pipeline...\n")
        queries = ["What are the key financial metrics?", "What are the main business risks?"]
        
        results = nlp_pipeline.process_document_segments(
            segments=segments,
            document_id=document_id,
            metadata=metadata,
            queries=queries
        )
        
        # Display results
        log_file.write("\n=== RAG CHATBOT RESULTS ===\n\n")
        
        if results:
            for key, value in results.items():
                log_file.write(f"\n== {key} ==\n")
                if isinstance(value, list):
                    for item in value:
                        log_file.write(f"- {item}\n")
                elif isinstance(value, dict):
                    for k, v in value.items():
                        log_file.write(f"- {k}: {v}\n")
                else:
                    log_file.write(f"{value}\n")
        else:
            log_file.write("No results generated\n")
            
        # Query stored insights
        log_file.write("\n=== STORED INSIGHTS ===\n\n")
        insights = storage.query_insights(document_id=document_id)
        for insight in insights:
            log_file.write(f"- {insight.get('metric_name', 'Unknown')}: {insight.get('value', 'N/A')}\n")
        
        log_file.write("\n=== PROCESSING COMPLETE ===\n")
        
    except Exception as e:
        log_file.write(f"\nError: {str(e)}\n")
        log_file.write(traceback.format_exc())

print("RAG chatbot pipeline execution complete. Results written to rag_final_run.txt")
