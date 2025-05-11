import os
import sys
import json
from datetime import datetime

from src.document_processor.processor import DocumentProcessor
from src.nlp_llm_pipeline.embedding import DocumentEmbedder
from src.nlp_llm_pipeline.retrieval import DocumentRetriever
from src.nlp_llm_pipeline.metric_extractor import MetricExtractor
from src.nlp_llm_pipeline.risk_identifier import RiskIdentifier
from src.nlp_llm_pipeline.sentiment_analyzer import SentimentAnalyzer

def main():
    print("=== FINANCIAL DOCUMENT END-TO-END TEST ===\n")
    start_time = datetime.now()
    
    # Initialize components
    print("Initializing components...")
    processor = DocumentProcessor()
    
    # Path to test document
    pdf_path = os.path.abspath("test_doc.pdf")
    print(f"Processing PDF: {pdf_path}")
    
    # STEP 1: Document Processing
    print("\n--- DOCUMENT PROCESSING ---")
    try:
        # Load document
        print("Loading document...")
        text_content = processor.load_document(pdf_path)
        print(f"Document loaded: {len(text_content)} characters")
        
        # Clean text
        print("Cleaning text...")
        cleaned_text = processor.clean_text(text_content)
        
        # Segment document
        print("Segmenting document...")
        segments = processor.segment_document(cleaned_text)
        print(f"Document segmented into {len(segments)} parts")
        
        # Print segment info
        for i, segment in enumerate(segments[:3]):  # Show first 3 segments
            print(f"  Segment {i+1}: {segment['section_type']} ({len(segment['text']):.0f} chars)")
        if len(segments) > 3:
            print(f"  ... and {len(segments)-3} more segments")
        
        # Extract tables
        tables = processor.extract_tables(cleaned_text)
        print(f"Found {len(tables)} tables in document")
        
    except Exception as e:
        print(f"ERROR in document processing: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # Create a document structure for NLP pipeline
    document = {
        "id": "test_doc_001",
        "content": cleaned_text,
        "segments": segments,
        "metadata": {
            "filename": "test_doc.pdf",
            "processing_date": datetime.now().isoformat(),
            "document_type": "10-K"
        }
    }
    
    # STEP 2: Save processed results
    print("\nSaving document results to disk...")
    os.makedirs("test_output", exist_ok=True)
    with open("test_output/processed_document.json", "w") as f:
        # Convert datetime to string
        doc_copy = document.copy()
        doc_copy["metadata"]["processing_date"] = document["metadata"]["processing_date"]
        json.dump(doc_copy, f, indent=2)
    
    print(f"\nTotal processing time: {datetime.now() - start_time}")
    print("\n=== PROCESSING COMPLETE ===")

if __name__ == "__main__":
    main()
