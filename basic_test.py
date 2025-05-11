#!/usr/bin/env python
"""
Very basic test script that writes to a file
Now testing with test_doc.pdf
"""

import os
import sys
import logging
from datetime import datetime

# Write to a file directly
with open("test_output.txt", "w") as f:
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
            f.write(f"PDF file found at {pdf_path}\n")  # Using test_doc.pdf
            doc = fitz.open(pdf_path)
            f.write(f"Opened PDF with {len(doc)} pages\n")
            
            # Get text from first page
            text = doc[0].get_text()
            f.write(f"First 200 chars of text: {text[:200]}\n")
        else:
            f.write(f"PDF file not found at {pdf_path}\n")
    except Exception as e:
        f.write(f"Error importing PyMuPDF or processing PDF: {str(e)}\n")
        
    # Try importing other key packages
    try:
        from langchain.llms import OpenAI
        f.write("Langchain imported successfully\n")
    except Exception as e:
        f.write(f"Error importing Langchain: {str(e)}\n")
        
    try:
        from src.config import LLM_CONFIG
        f.write(f"Config imported successfully: {LLM_CONFIG}\n")
    except Exception as e:
        f.write(f"Error importing config: {str(e)}\n")

print("Script completed, check test_output.txt for results")
