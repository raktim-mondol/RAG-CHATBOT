import os
import sys
import traceback

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from check_pdf import check_pdf
from src.document_processor.processor import DocumentProcessor

def run_document_processor_test():
    """Run end-to-end test on the document processor."""
    print("\n=== DOCUMENT PROCESSOR TEST ===")
    
    # First check if the PDF is valid
    if not check_pdf():
        print("PDF check failed, cannot continue with document processor test")
        return False
    
    # Initialize the document processor
    try:
        processor = DocumentProcessor()
        print("\nDocumentProcessor initialized successfully")
    except Exception as e:
        print(f"Failed to initialize DocumentProcessor: {e}")
        traceback.print_exc()
        return False
    
    # Load the document
    pdf_path = os.path.join(os.path.dirname(__file__), "test_doc.pdf")
    print(f"\nLoading document: {pdf_path}")
    try:
        content = processor.load_document(pdf_path)
        print(f"Document loaded successfully: {len(content)} characters")
        print(f"Content sample: {content[:200]}...")
    except Exception as e:
        print(f"Failed to load document: {e}")
        traceback.print_exc()
        return False
    
    # Clean the text
    print("\nCleaning document text...")
    try:
        cleaned_text = processor.clean_text(content)
        print(f"Text cleaned successfully: {len(cleaned_text)} characters")
        print(f"Cleaned sample: {cleaned_text[:200]}...")
    except Exception as e:
        print(f"Failed to clean text: {e}")
        traceback.print_exc()
        return False
        
    # Segment the document
    print("\nSegmenting document...")
    try:
        segments = processor.segment_document(cleaned_text)
        print(f"Document segmented successfully into {len(segments)} segments")
        
        # Show segment details
        for i, segment in enumerate(segments[:3]):  # Show first 3 segments
            print(f"\nSegment {i+1}:")
            print(f"  Type: {segment['section_type']}")
            print(f"  Length: {len(segment['text'])} chars")
            print(f"  Pages: {segment['start_page']} to {segment['end_page']}")
            print(f"  Sample: {segment['text'][:100]}...")
            
        if len(segments) > 3:
            print(f"\n...and {len(segments) - 3} more segments")
    except Exception as e:
        print(f"Failed to segment document: {e}")
        traceback.print_exc()
        return False
    
    # Extract tables
    print("\nExtracting tables...")
    try:
        tables = processor.extract_tables(cleaned_text)
        print(f"Tables extracted successfully: found {len(tables)} tables")
        
        # Show table details
        for i, table in enumerate(tables[:2]):  # Show first 2 tables
            print(f"\nTable {i+1}:")
            print(f"  Rows: {len(table)}")
            for j, row in enumerate(table[:3]):  # Show first 3 rows
                print(f"  Row {j+1}: {row}")
            if len(table) > 3:
                print(f"  ...and {len(table) - 3} more rows")
                
        if len(tables) > 2:
            print(f"\n...and {len(tables) - 2} more tables")
    except Exception as e:
        print(f"Failed to extract tables: {e}")
        traceback.print_exc()
        return False
    
    # Save output to files
    output_dir = os.path.join(os.path.dirname(__file__), "test_outputs")
    os.makedirs(output_dir, exist_ok=True)
    
    # Save the cleaned text
    with open(os.path.join(output_dir, "cleaned_text.txt"), "w", encoding="utf-8") as f:
        f.write(cleaned_text)
    
    # Save segment information
    with open(os.path.join(output_dir, "segments_info.txt"), "w", encoding="utf-8") as f:
        f.write(f"Total segments: {len(segments)}\n\n")
        for i, segment in enumerate(segments):
            f.write(f"Segment {i+1}:\n")
            f.write(f"  Type: {segment['section_type']}\n")
            f.write(f"  Length: {len(segment['text'])} chars\n")
            f.write(f"  Pages: {segment['start_page']} to {segment['end_page']}\n")
            f.write(f"  Sample: {segment['text'][:100]}...\n\n")
    
    print("\n=== DOCUMENT PROCESSOR TEST COMPLETED SUCCESSFULLY ===")
    print(f"Output files saved to: {output_dir}")
    return True

if __name__ == "__main__":
    run_document_processor_test()
