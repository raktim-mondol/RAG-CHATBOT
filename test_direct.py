import os
import sys
from src.document_processor.processor import DocumentProcessor

def main():
    # Initialize document processor
    processor = DocumentProcessor()
    
    # Path to test document
    pdf_path = os.path.abspath("test_doc.pdf")
    print(f"Processing PDF: {pdf_path}")
    
    # Test if file exists
    if not os.path.exists(pdf_path):
        print(f"ERROR: File not found: {pdf_path}")
        return
    
    print("File exists, beginning processing...")
    
    try:
        # Load and process document
        print("Step 1: Loading document...")
        text_content = processor.load_document(pdf_path)
        print(f"Document loaded, extracted {len(text_content)} characters")
        print("\nFirst 200 characters of content:")
        print(text_content[:200])
        
        print("\nStep 2: Cleaning text...")
        cleaned_text = processor.clean_text(text_content)
        print(f"Text cleaned, now {len(cleaned_text)} characters")
        
        print("\nStep 3: Segmenting document...")
        segments = processor.segment_document(cleaned_text)
        print(f"Document segmented into {len(segments)} parts")
        
        print("\nSegment types found:")
        for i, segment in enumerate(segments):
            print(f"  {i+1}. {segment['section_type']} ({len(segment['text'])} chars)")
        
        print("\nStep 4: Looking for tables...")
        tables = processor.extract_tables(cleaned_text)
        print(f"Found {len(tables)} tables in document")
        
        print("\nProcessing complete!")
        
    except Exception as e:
        print(f"ERROR during processing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
