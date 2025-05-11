"""
Direct OpenAI API Call - Test 10-K query without using the full RAG pipeline
"""

import os
import sys
import requests
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import DocumentProcessor and config
from src.document_processor.processor import DocumentProcessor
from src.config import LLM_CONFIG

def main():
    print("\n=== DIRECT API TEST WITH GPT-4o-mini ===")
    
    # 1. Check API key
    api_key = LLM_CONFIG.get("api_key")
    if not api_key:
        print("ERROR: No OpenAI API key found. Please set OPENAI_API_KEY in config.py")
        return
    
    print(f"Using model: {LLM_CONFIG['model']}")
    
    # 2. Load document
    print("\nLoading document...")
    processor = DocumentProcessor()
    pdf_path = os.path.abspath("test_doc.pdf")
    
    try:
        text = processor.load_document(pdf_path)
        text = processor.clean_text(text)
        print(f"Document loaded and cleaned: {len(text)} characters")
    except Exception as e:
        print(f"Error loading document: {e}")
        return
    
    # 3. Extract a sample chunk (first 8000 tokens should be safe for context)
    context = text[:16000]  # Roughly 4000-5000 tokens
    
    # 4. Define query
    query = "What was Continental Resources' total revenue for the most recent year and how does it compare to the previous year?"
    
    print(f"\nQuery: {query}")
    print("\nGenerating response with direct API call...")
    
    # 5. Create prompt for RAG
    prompt = f"""
You are a financial analyst specialized in extracting information from 10-K reports.
I'm going to provide you with a section from Continental Resources' 10-K report.
Please answer the question based ONLY on the information in the provided text.

QUESTION: {query}

DOCUMENT EXCERPT:
{context}

Answer:
"""
    
    # 6. Make direct API call
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        data = {
            "model": LLM_CONFIG["model"],
            "messages": [
                {"role": "system", "content": "You are a financial analyst specialized in extracting information from 10-K reports."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 500
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data
        )
        
        if response.status_code != 200:
            print(f"Error from API: {response.status_code}")
            print(response.text)
            return
        
        # 7. Extract and print answer
        result = response.json()
        answer = result["choices"][0]["message"]["content"].strip()
        
        print("\n=== RESPONSE ===")
        print(answer)
        print("================")
        
        # 8. Save results
        os.makedirs("rag_results", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join("rag_results", f"direct_api_{timestamp}.txt")
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("=== DIRECT API TEST RESULTS ===\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Model: {LLM_CONFIG['model']}\n")
            f.write(f"Query: {query}\n\n")
            f.write("Response:\n")
            f.write(answer)
            
        print(f"\nResults saved to {output_file}")
        
    except Exception as e:
        print(f"Error making OpenAI API call: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
