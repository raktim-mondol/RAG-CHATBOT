#!/usr/bin/env python
"""
Minimal script to verify PDF processing capability
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

def test_pdf_processing():
    """Test if we can process a PDF file"""
    
    print("Starting test_run.py")
    
    # PDF file path
    pdf_path = os.path.join(os.path.dirname(__file__), "test_doc.pdf")
    print(f"PDF path: {pdf_path}")
    
    # Check if file exists
    if not os.path.exists(pdf_path):
        print(f"Error: File not found at {pdf_path}")
        return False
    
    print(f"Found PDF file at: {pdf_path}")
    
    try:
        # Try to read the PDF content using PyMuPDF
        import fitz
        print("Importing PyMuPDF (fitz) successful")
        
        doc = fitz.open(pdf_path)
        print(f"Opened PDF with {len(doc)} pages")
        
        text = ""
        for i, page in enumerate(doc):
            text += page.get_text()
            if i == 0:  # Just read first page for test
                break
                
        # Show first 200 characters of extracted text
        print(f"Successfully extracted text from PDF. First 200 chars: {text[:200]}")
        
        return True
        
    except Exception as e:
        print(f"Error processing PDF: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_pdf_processing()
    if success:
        print("PDF processing successful!")
    else:
        print("PDF processing failed!")
