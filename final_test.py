#!/usr/bin/env python
"""
Final test script with proper encoding
"""

import os
import sys
import logging
from datetime import datetime

# Write to a file directly with UTF-8 encoding to handle special characters
with open("test_output.txt", "w", encoding="utf-8") as f:
    f.write(f"Test run at {datetime.now()}\n")
    f.write(f"Python executable: {sys.executable}\n")
    f.write(f"Python version: {sys.version}\n")
    
    # Try to import key packages
    try:
        import fitz
        f.write("PyMuPDF (fitz) imported successfully\n")
        
        # Try to open the PDF
        pdf_path = os.path.join(os.path.dirname(__file__), "test_doc.pdf")
        if os.path.exists(pdf_path):
            f.write(f"PDF file found at {pdf_path}\n")
            doc = fitz.open(pdf_path)
            f.write(f"Opened PDF with {len(doc)} pages\n")
            
            # Get text from first page - handle encoding safely
            try:
                text = doc[0].get_text()
                f.write(f"Successfully extracted text from first page (length: {len(text)} chars)\n")
                f.write("First 100 chars (safely encoded): " + text[:100].encode('ascii', 'replace').decode('ascii') + "\n")
            except Exception as text_e:
                f.write(f"Error extracting text: {str(text_e)}\n")
        else:
            f.write(f"PDF file not found at {pdf_path}\n")
    except Exception as e:
        f.write(f"Error importing PyMuPDF or processing PDF: {str(e)}\n")
        
    # Try importing src.ingestion_pipeline
    try:
        from src.ingestion_pipeline.ingest import IngestionPipeline
        f.write("IngestionPipeline imported successfully\n")
    except Exception as e:
        f.write(f"Error importing IngestionPipeline: {str(e)}\n")
        
    # Try importing src.nlp_llm_pipeline
    try:
        from src.nlp_llm_pipeline.pipeline import NLPLlmPipeline
        f.write("NLPLlmPipeline imported successfully\n")
    except Exception as e:
        f.write(f"Error importing NLPLlmPipeline: {str(e)}\n")
        
    # Try importing config
    try:
        from src.config import LLM_CONFIG
        f.write(f"Config imported successfully: {LLM_CONFIG}\n")
    except Exception as e:
        f.write(f"Error importing config: {str(e)}\n")

print("Script completed, check test_output.txt for results")
