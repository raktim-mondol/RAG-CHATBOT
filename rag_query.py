import os
import sys
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
# Import openai for older version compatibility
import openai

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configure OpenAI API 
openai.api_key = os.getenv("OPENAI_API_KEY")
print(f"Using API key: {openai.api_key[:10]}...{openai.api_key[-5:]}")
model_name = "gpt-4o-mini"  # Force using GPT-4o-mini
print(f"Using model: {model_name}")
temperature = float(os.getenv("LLM_TEMPERATURE", 0.7))
print(f"Using temperature: {temperature}")

class SimpleRAG:
    def __init__(self, document_path="test_outputs/cleaned_text.txt"):
        """Initialize the RAG system with a document."""
        self.document_path = document_path
        self.client = openai  # Use the openai module directly for older version
        
        # Load the document content
        try:
            with open(document_path, 'r', encoding='utf-8') as f:
                self.document_content = f.read()
            logger.info(f"Loaded document: {len(self.document_content)} characters")
        except Exception as e:
            logger.error(f"Failed to load document: {e}")
            self.document_content = ""
    
    def chunk_document(self, chunk_size=8000, overlap=200):
        """Split document into manageable chunks."""
        content = self.document_content
        chunks = []
        
        # Simple chunking by character count
        for i in range(0, len(content), chunk_size - overlap):
            chunk = content[i:i + chunk_size]
            chunks.append(chunk)
            
            # Don't go past the end of the document
            if i + chunk_size >= len(content):
                break
                
        logger.info(f"Document split into {len(chunks)} chunks")
        return chunks
    
    def simple_keyword_search(self, query, chunks):
        """Basic keyword-based retrieval."""
        query_terms = query.lower().split()
        results = []
        
        for i, chunk in enumerate(chunks):
            chunk_lower = chunk.lower()
            score = sum(chunk_lower.count(term) for term in query_terms)
            results.append((i, score, chunk))
        
        # Sort by score, highest first
        results.sort(key=lambda x: x[1], reverse=True)
        return results
    
    def query(self, user_query, top_k=3):
        """Process a user query and generate a response."""
        # Step 1: Split the document into chunks
        chunks = self.chunk_document()
        
        # Step 2: Retrieve relevant chunks
        ranked_chunks = self.simple_keyword_search(user_query, chunks)
        
        # Step 3: Take top-k chunks
        top_chunks = ranked_chunks[:top_k]
        
        # Log the top chunks and their scores
        for i, (chunk_idx, score, _) in enumerate(top_chunks):
            logger.info(f"Top chunk {i+1} (idx: {chunk_idx}, score: {score})")
        
        # Step 4: Create a context from top chunks
        context = "\n\n---\n\n".join([chunk for _, _, chunk in top_chunks])
        
        # Step 5: Create a prompt for the LLM
        prompt = f"""You are a financial analyst assistant. Answer the question based on the provided context from a financial document (10-K).

Context from the document:
{context}

Question: {user_query}

Provide a detailed, well-structured answer. If the information cannot be found in the context, state that clearly."""
          # Step 6: Call the OpenAI API
        try:
            logger.info(f"Calling OpenAI API with model: {model_name}")
            # For OpenAI version 0.28.0, use the completions API differently
            response = self.client.ChatCompletion.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a financial analyst assistant that provides accurate information based on the context provided."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=1000
            )
              # Step 7: Return the response
            answer = response.choices[0].message.content
            logger.info(f"Generated response: {len(answer)} characters")
            return answer
            
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            return f"Error generating response: {str(e)}"

def run_rag_query():
    """Run a RAG query on the processed document."""
    # Create output directory if it doesn't exist
    os.makedirs("rag_results", exist_ok=True)
    
    # Create a timestamp for the output file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"rag_results/rag_query_{timestamp}.txt"
    
    # Initialize the RAG system
    rag = SimpleRAG()
    
    # List of queries to run
    queries = [
        "What are main business operations?",
        "What were the total revenues in the most recent fiscal year?",
        "What are the key risk factors mentioned in the document?",
        "Summarize the company's financial performance over the last year.",
        "What is the company's long term strategy for growth?"
    ]
    
    # Process each query and save results
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=== RAG QUERY RESULTS ===\n\n")
        f.write(f"Document: test_doc.pdf (Continental Resources 10-K)\n")
        f.write(f"Model: {model_name}\n")
        f.write(f"Temperature: {temperature}\n")
        f.write(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        for i, query in enumerate(queries, 1):
            print(f"\nProcessing query {i}/{len(queries)}: {query}")
            f.write(f"Query {i}: {query}\n")
            f.write("-" * 80 + "\n\n")
            
            # Get the response
            response = rag.query(query)
            
            # Write to file and print to console
            f.write(response + "\n\n")
            print(f"\nAnswer:\n{response}\n")
            
            # Add separator between queries
            if i < len(queries):
                f.write("=" * 80 + "\n\n")
    
    print(f"\nResults saved to: {output_file}")
    return output_file

if __name__ == "__main__":
    output_path = run_rag_query()
