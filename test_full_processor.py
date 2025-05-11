import os
import sys
import json
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.document_processor.processor import DocumentProcessor

def main():
    print("=== TEST DOCUMENT PROCESSOR END-TO-END ===\n")
    start_time = datetime.now()
    
    # Initialize document processor
    processor = DocumentProcessor()
    
    # Path to test document
    pdf_path = os.path.abspath("test_doc.pdf")
    print(f"Testing PDF: {pdf_path}")
    
    if not os.path.exists(pdf_path):
        print(f"ERROR: File not found: {pdf_path}")
        return
    
    # STEP 1: Load document
    print("\nStep 1: Loading document...")
    try:
        text_content = processor.load_document(pdf_path)
        print(f"Success! Document loaded with {len(text_content)} characters")
        print(f"Text sample: {text_content[:100]}...")
    except Exception as e:
        print(f"FAILED: Unable to load document: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # STEP 2: Clean text
    print("\nStep 2: Cleaning text...")
    try:
        cleaned_text = processor.clean_text(text_content)
        print(f"Success! Text cleaned, now {len(cleaned_text)} characters")
        print(f"Cleaned sample: {cleaned_text[:100]}...")
    except Exception as e:
        print(f"FAILED: Unable to clean text: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # STEP 3: Segment document
    print("\nStep 3: Segmenting document...")
    try:
        segments = processor.segment_document(cleaned_text)
        print(f"Success! Document segmented into {len(segments)} parts")
        
        # Print segment info
        for i, segment in enumerate(segments[:3]):  # Show first 3 segments
            print(f"  Segment {i+1}: {segment['section_type']} ({len(segment['text'])} chars)")
        if len(segments) > 3:
            print(f"  ... and {len(segments)-3} more segments")
    except Exception as e:
        print(f"FAILED: Unable to segment document: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # STEP 4: Extract tables
    print("\nStep 4: Extracting tables...")
    try:
        tables = processor.extract_tables(cleaned_text)
        print(f"Success! Found {len(tables)} tables in document")
        
        # Print table info
        for i, table in enumerate(tables[:2]):  # Show first 2 tables
            print(f"  Table {i+1}: {len(table)} rows")
            for row in table[:2]:  # Show first 2 rows
                print(f"    {row}")
            if len(table) > 2:
                print(f"    ... and {len(table)-2} more rows")
        if len(tables) > 2:
            print(f"  ... and {len(tables)-2} more tables")
    except Exception as e:
        print(f"FAILED: Unable to extract tables: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # Save results
    print("\nSaving results...")
    os.makedirs("test_output", exist_ok=True)
    
    # Save document text
    with open("test_output/document.txt", "w", encoding="utf-8") as f:
        f.write(cleaned_text)
    
    # Save segments
    with open("test_output/segments.json", "w", encoding="utf-8") as f:
        json.dump(segments, f, indent=2)
    
    print(f"\nTotal processing time: {datetime.now() - start_time}")
    print("\n=== TEST COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    main()
