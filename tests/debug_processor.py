import os
import sys
import json

# Add the project root to Python's module search path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the DocumentProcessor
from src.document_processor.processor import DocumentProcessor

# Define the main function
def test_document_processor():
    """Test all major functions of the DocumentProcessor class."""
    print("=== DOCUMENT PROCESSOR TEST ===")
    
    # Initialize processor
    processor = DocumentProcessor()
    print("DocumentProcessor initialized")
    
    # Set up paths
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pdf_path = os.path.join(base_path, "test_doc.pdf")
    print(f"Looking for PDF at: {pdf_path}")
    
    # Check if file exists
    if not os.path.exists(pdf_path):
        print(f"ERROR: File not found: {pdf_path}")
        sys.exit(1)
    else:
        print(f"File found, size: {os.path.getsize(pdf_path) / 1024:.2f} KB")
    
    # 1. Test load_document
    print("\nTEST: load_document()")
    try:
        text = processor.load_document(pdf_path)
        print(f"SUCCESS: Loaded document with {len(text)} characters")
        print(f"Sample content: {text[:150]}...")
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # 2. Test clean_text
    print("\nTEST: clean_text()")
    try:
        cleaned_text = processor.clean_text(text)
        print(f"SUCCESS: Cleaned text, now {len(cleaned_text)} characters")
        print(f"Sample cleaned content: {cleaned_text[:150]}...")
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # 3. Test segment_document
    print("\nTEST: segment_document()")
    try:
        segments = processor.segment_document(cleaned_text)
        print(f"SUCCESS: Segmented document into {len(segments)} segments")
        if segments:
            print(f"First segment type: '{segments[0]['section_type']}'")
            print(f"First segment text (sample): {segments[0]['text'][:100]}...")
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # 4. Test extract_tables
    print("\nTEST: extract_tables()")
    try:
        tables = processor.extract_tables(cleaned_text)
        print(f"SUCCESS: Found {len(tables)} tables")
        if tables:
            print(f"First table has {len(tables[0])} rows")
            print(f"First few rows: {tables[0][:3]}")
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n=== ALL TESTS PASSED ===")

# Run the test
if __name__ == "__main__":
    test_document_processor()
