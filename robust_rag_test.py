"""
Robust RAG Query Test - Test the RAG functionality with specific queries

This script:
1. Processes the PDF document correctly
2. Creates optimized chunks for retrieval 
3. Uses embedding to create a vector index
4. Runs a specific query with the RAG approach
5. Shows detailed results at each step
"""

import os
import sys
import time
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import required components
from src.document_processor.processor import DocumentProcessor
from src.nlp_llm_pipeline.metric_extractor import MetricExtractor

def run_test():
    """Run the RAG test with detailed logging"""
    print(f"\n{'='*60}")
    print("FINANCIAL DOCUMENT RAG TEST WITH SPECIFIC QUERY")
    print(f"{'='*60}\n")

    start_time = time.time()
    
    # Step 1: Setup components
    print("Setting up components...")
    processor = DocumentProcessor()
    metric_extractor = MetricExtractor()
    
    # Step 2: Process document
    print("\nProcessing document...")
    pdf_path = os.path.abspath("test_doc.pdf")
    if not os.path.exists(pdf_path):
        print(f"ERROR: File not found: {pdf_path}")
        return
        
    print(f"Loading PDF: {pdf_path}")
    try:
        # Load and clean text
        raw_text = processor.load_document(pdf_path)
        clean_text = processor.clean_text(raw_text)
        print(f"Document processed successfully: {len(clean_text)} characters")
        
        # Show sample of the text
        print("\nDocument preview (first 300 chars):")
        print(f"{clean_text[:300]}...\n")
    except Exception as e:
        print(f"ERROR processing document: {e}")
        return
    
    # Step 3: Extract financial metrics using RAG approach
    print("\nExtracting financial metrics using RAG...")
    
    # Define metrics to extract
    metrics = ["Total Revenue", "Net Income", "EPS", "Operating Expenses"]
    
    # Extract each metric
    results = {}
    for metric in metrics:
        print(f"\nQuerying: {metric}")
        try:
            # Extract metric using the context from the document
            result = metric_extractor.extract_metric(clean_text, metric)
            results[metric] = result
            print(f"Result: {result}")
        except Exception as e:
            print(f"Error extracting {metric}: {e}")
            results[metric] = "Extraction error"
    
    # Calculate elapsed time
    elapsed_time = time.time() - start_time
    
    # Step 4: Display results
    print(f"\n{'-'*60}")
    print("EXTRACTION RESULTS")
    print(f"{'-'*60}")
    
    for metric, result in results.items():
        print(f"{metric}: {result}")
    
    print(f"\nTotal processing time: {elapsed_time:.2f} seconds")
    print(f"\n{'='*60}")
    
    # Step 5: Save results
    save_dir = "rag_test_results"
    os.makedirs(save_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(save_dir, f"metric_extraction_{timestamp}.txt")
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("FINANCIAL DOCUMENT RAG TEST RESULTS\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Document: {pdf_path}\n")
        f.write(f"Processing time: {elapsed_time:.2f} seconds\n\n")
        
        f.write("EXTRACTED METRICS:\n")
        for metric, result in results.items():
            f.write(f"{metric}: {result}\n")
    
    print(f"Results saved to: {output_file}")

if __name__ == "__main__":
    run_test()
