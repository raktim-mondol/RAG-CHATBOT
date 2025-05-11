"""
RAG Query Test Script - Test RAG functionality with gpt-4o-mini model

This script:
1. Loads our already processed PDF (test_doc.pdf)
2. Initializes the document processor, embedding model and retriever
3. Creates embeddings and stores them in a FAISS index
4. Runs a sample query against the document using the RAG approach
5. Outputs the retrieved context and the final LLM-generated response
"""

import os
import sys
import time
from datetime import datetime

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import required components
from src.document_processor.processor import DocumentProcessor
from src.nlp_llm_pipeline.embedding import FinancialEmbeddings
from src.nlp_llm_pipeline.retrieval import DocumentRetriever
from src.nlp_llm_pipeline.metric_extractor import MetricExtractor
from src.nlp_llm_pipeline.sentiment_analyzer import SentimentAnalyzer
from src.nlp_llm_pipeline.risk_identifier import RiskIdentifier
from src.nlp_llm_pipeline.summary_generator import SummaryGenerator
from src.config import LLM_CONFIG

def run_rag_test():
    """Run a full RAG test on the test_doc.pdf"""
    print("\n=== RAG QUERY TEST ===")
    print("Testing retrieval-augmented generation on Continental Resources 10-K document")
    print(f"Using LLM model: {LLM_CONFIG['model']}")
    print("Date:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("-" * 50)
    
    # Step 1: Load the document
    start_time = time.time()
    print("\n1. Loading and processing document...")
    
    processor = DocumentProcessor()
    pdf_path = os.path.abspath("test_doc.pdf")
    
    if not os.path.exists(pdf_path):
        print(f"ERROR: PDF file not found at {pdf_path}")
        return
    
    # Process the document
    text_content = processor.load_document(pdf_path)
    cleaned_text = processor.clean_text(text_content)
    segments = processor.segment_document(cleaned_text)
    
    print(f"✓ Document loaded and processed: {len(cleaned_text)} chars, {len(segments)} segments")
    
    # Step 2: Set up embedding and retrieval
    print("\n2. Initializing embeddings and retrieval components...")
    embeddings_model = FinancialEmbeddings()
    retriever = DocumentRetriever(embeddings_model)
    
    # Step 3: Create document index
    print("\n3. Creating document index...")
    
    # Extract text from segments or use the full document
    if segments and len(segments) > 0:
        segment_texts = [segment["text"] for segment in segments]
        print(f"Creating index with {len(segment_texts)} segments")
    else:
        segment_texts = [cleaned_text]
        print("Creating index with full document (no segments found)")
    
    # Create the index
    retriever.create_index(segment_texts)
    print("✓ Document indexed successfully")
    
    # Step 4: Initialize LLM components
    print("\n4. Setting up LLM components...")
    
    # Check OpenAI API key
    if not LLM_CONFIG["api_key"]:
        print("ERROR: No OpenAI API key found. Please set the OPENAI_API_KEY environment variable.")
        return
    
    # Initialize specialized LLM components
    metric_extractor = MetricExtractor()
    sentiment_analyzer = SentimentAnalyzer()
    risk_identifier = RiskIdentifier()
    summary_generator = SummaryGenerator()
    
    print("✓ LLM components initialized")
    
    # Step 5: Define test queries
    print("\n5. Running test queries...")
    test_queries = [
        "What was Continental Resources' total revenue in the past year?",
        "What are the main risk factors for Continental Resources?",
        "Summarize Continental Resources' business strategy"
    ]
    
    # Step 6: Process and answer each query
    results = {}
    for i, query in enumerate(test_queries):
        print(f"\n--- QUERY {i+1}: {query}")
        
        # Retrieve relevant context using RAG
        contexts = retriever.retrieve_context(query, k=3)
        print(f"Retrieved {len(contexts)} relevant document segments")
        
        context_text = "\n".join(contexts)
        print(f"Context length: {len(context_text)} characters")
        
        # Process query based on its nature
        if "revenue" in query.lower() or "income" in query.lower() or "profit" in query.lower():
            print("Processing as metric extraction query...")
            metric_name = query.split("'s ")[-1].split(" in")[0]
            response = metric_extractor.extract_metric(context_text, metric_name)
            
        elif "risk" in query.lower():
            print("Processing as risk identification query...")
            response = risk_identifier.identify_risks(context_text)
            
        elif "summarize" in query.lower() or "summary" in query.lower():
            print("Processing as summarization query...")
            response = summary_generator.generate_summary(context_text)
            
        else:
            # Default to summary
            print("Processing as general query...")
            response = summary_generator.generate_summary(context_text)
        
        print("\nANSWER:")
        print(response)
        print("-" * 50)
        
        # Store results
        results[query] = {
            "context_length": len(context_text),
            "response": response
        }
    
    # Calculate and print timing
    elapsed_time = time.time() - start_time
    print(f"\nProcessing completed in {elapsed_time:.2f} seconds")
    
    # Save the results to a file
    output_dir = "rag_test_results"
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = os.path.join(output_dir, f"rag_results_{timestamp}.txt")
    
    with open(result_file, "w", encoding="utf-8") as f:
        f.write("=== RAG QUERY TEST RESULTS ===\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Model: {LLM_CONFIG['model']}\n")
        f.write(f"Document: test_doc.pdf (Continental Resources 10-K)\n")
        f.write(f"Processing time: {elapsed_time:.2f} seconds\n\n")
        
        for i, (query, result) in enumerate(results.items()):
            f.write(f"QUERY {i+1}: {query}\n")
            f.write(f"Context size: {result['context_length']} characters\n")
            f.write("RESPONSE:\n")
            f.write(f"{result['response']}\n\n")
            f.write("-" * 50 + "\n\n")
    
    print(f"\nResults saved to {result_file}")
    print("\n=== TEST COMPLETED ===")

if __name__ == "__main__":
    run_rag_test()
