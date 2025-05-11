"""
Simple RAG Query - Test a specific question against the Continental Resources 10-K document
"""

import os
import sys
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import required components
from src.document_processor.processor import DocumentProcessor
from src.nlp_llm_pipeline.embedding import FinancialEmbeddings
from src.nlp_llm_pipeline.retrieval import DocumentRetriever
from src.nlp_llm_pipeline.summary_generator import SummaryGenerator
from src.config import LLM_CONFIG

def main():
    print("=== SIMPLE RAG QUERY TEST ===")
    print(f"Using model: {LLM_CONFIG['model']}")
    
    # Check OpenAI API key
    if not LLM_CONFIG["api_key"]:
        print("ERROR: OpenAI API key not found in environment variables.")
        print("Please set OPENAI_API_KEY first.")
        return

    # Step 1: Load and process the document
    print("\nStep 1: Processing document...")
    pdf_path = os.path.abspath("test_doc.pdf")
    processor = DocumentProcessor()
    
    try:
        raw_text = processor.load_document(pdf_path)
        clean_text = processor.clean_text(raw_text)
        print(f"Document processed: {len(clean_text)} characters")
    except Exception as e:
        print(f"Error processing document: {e}")
        return

    # Step 2: Set up embedding and retrieval
    print("\nStep 2: Setting up embedding and retrieval...")
    embeddings = FinancialEmbeddings()
    retriever = DocumentRetriever(embeddings)
    
    # Create document chunks (500-word chunks with 50-word overlap)
    print("Splitting document into chunks...")
    words = clean_text.split()
    chunk_size = 1000
    overlap = 100
    chunks = []
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i+chunk_size])
        chunks.append(chunk)
        
    print(f"Document split into {len(chunks)} chunks")
    
    # Create search index
    print("Creating search index...")
    retriever.create_index(chunks)

    # Step 3: Execute a query
    print("\nStep 3: Executing query...")
    query = "What is Continental Resources' total revenue for 2022 and how does it compare to 2021?"
    
    print(f"Query: {query}")
    print("Retrieving relevant context...")
    contexts = retriever.retrieve_context(query, k=3)
    
    print(f"Retrieved {len(contexts)} context chunks")
    
    # Combine contexts
    combined_context = "\n\n".join(contexts)
    print(f"Combined context: {len(combined_context)} characters")

    # Step 4: Generate response with LLM
    print("\nStep 4: Generating response with LLM...")
    summary_gen = SummaryGenerator()
    
    try:
        response = summary_gen.generate_summary(
            f"Question: {query}\n\nContext from financial document:\n{combined_context}"
        )
        
        print("\n=== RAG QUERY RESPONSE ===")
        print(response)
        print("\n=========================")
        
        # Save to file
        os.makedirs("rag_results", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        with open(f"rag_results/query_result_{timestamp}.txt", "w", encoding="utf-8") as f:
            f.write("=== SIMPLE RAG QUERY TEST ===\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Model: {LLM_CONFIG['model']}\n\n")
            f.write(f"Query: {query}\n\n")
            f.write("Context (first 500 chars of each chunk):\n")
            for i, ctx in enumerate(contexts):
                f.write(f"--- Context Chunk {i+1} ---\n")
                f.write(f"{ctx[:500]}...\n\n")
            f.write("=== Response ===\n")
            f.write(response)
            
        print(f"\nResults saved to rag_results/query_result_{timestamp}.txt")
    except Exception as e:
        print(f"Error generating response: {e}")

if __name__ == "__main__":
    main()
