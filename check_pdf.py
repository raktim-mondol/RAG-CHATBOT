import os
import sys
import traceback

def check_pdf():
    """Check if the PDF file can be opened and processed correctly."""
    print("=== PDF FILE CHECK ===")
    
    # Check if pymupdf is installed
    try:
        import fitz  # PyMuPDF
        print("PyMuPDF (fitz) is installed")
    except ImportError:
        print("ERROR: PyMuPDF (fitz) is not installed. Please run: pip install pymupdf")
        return False
        
    pdf_path = os.path.join(os.path.dirname(__file__), "test_doc.pdf")
    print(f"Checking PDF file: {pdf_path}")
    
    # Check if file exists
    if not os.path.exists(pdf_path):
        print(f"ERROR: File not found: {pdf_path}")
        return False
    
    print(f"File exists, size: {os.path.getsize(pdf_path) / 1024:.2f} KB")
    
    # Try to open with PyMuPDF
    try:
        doc = fitz.open(pdf_path)
        page_count = len(doc)
        print(f"Successfully opened PDF with {page_count} pages")
        
        # Try to extract text from first page
        first_page = doc.load_page(0)
        text = first_page.get_text()
        print(f"First page text sample: {text[:150]}...")
          # Show document info
        print(f"\nDocument info:")
        print(f"  Format: {doc.name}")
        print(f"  Page count: {page_count}")
        print(f"  File size: {os.path.getsize(pdf_path) / 1024:.2f} KB")
        
        # Get metadata
        metadata = doc.metadata
        print("\nMetadata:")
        for key, value in metadata.items():
            if value:  # Only print non-empty values
                print(f"  {key}: {value}")
        
        print("\nPDF CHECK SUCCESSFUL")
        return True
        
    except Exception as e:
        print(f"ERROR opening PDF: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    check_pdf()
