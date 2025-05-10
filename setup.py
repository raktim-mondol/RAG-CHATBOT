#!/usr/bin/env python
"""
Setup script for Financial Document Intelligence System
This script initializes the database schema and loads sample data for testing.
"""
import os
import sys
import datetime
import argparse

# Add project root to path to allow imports from src
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from src.storage_access import storage  # Imports the new MongoDB storage module
from src.config import MONGO_CONFIG  # Updated to MONGO_CONFIG
from src.nlp_llm_pipeline.pipeline import NLPLlmPipeline
from src.ingestion_pipeline.ingest import IngestionPipeline

def initialize_database():
    """Initialize the MongoDB database (collections and indexes)."""
    print("Initializing MongoDB database...")
    storage.connect_to_mongo()  # Ensures connection and calls initialize_database internally
    print("MongoDB database initialized successfully.")

def create_demo_document():
    """Create a sample financial document for demo purposes."""
    print("Creating demo document...")
    
    # Sample document metadata
    document_data = {
        'company': 'Demo Corp',
        'doc_type': '10-K',
        'filing_date': datetime.datetime.now().isoformat(),  # Store as ISO format string
        'source_url': 'https://example.com/demo-financials',
        'file_path': 'demo_document.txt',
        'processed': True
    }
    
    # Save document to database
    document_id = storage.save_document(document_data)
    
    if document_id:
        print(f"Demo document created with ID: {document_id}")
        
        # Create sample document segments
        segments = [
            {
                'section_type': 'Summary',
                'text': "Demo Corp reported strong financial results for the fiscal year ended December 31, 2024. "
                        "Total revenue increased to $1.5 billion, representing a 15% growth year-over-year. "
                        "Net income was $320 million, up 20% from the previous year. "
                        "Earnings per share (EPS) was $3.45.",
                'start_page': 1,
                'end_page': 1
            },
            {
                'section_type': 'Risk Factors',
                'text': "The company faces risks related to market competition, regulatory changes, and currency fluctuations. "
                        "In particular, trade tensions between major economies could impact supply chains and pricing. "
                        "Additionally, rising interest rates may increase borrowing costs and affect capital expenditure plans.",
                'start_page': 2,
                'end_page': 3
            },
            {
                'section_type': 'Financial Data',
                'text': "Key financial metrics (in millions unless specified):\n"
                        "- Total Revenue: $1,500\n"
                        "- Operating Expenses: $950\n"
                        "- Operating Profit: $550\n"
                        "- Net Income: $320\n"
                        "- EPS: $3.45\n"
                        "- Debt to Equity Ratio: 0.4",
                'start_page': 4,
                'end_page': 5
            }
        ]
        
        # Save segments to database
        storage.save_segments(segments, document_id)
        print("Demo document segments created.")
        
        return document_id, segments
    else:
        print("Failed to create demo document.")
        return None, None

def extract_insights(document_id, segments):
    """Extract insights from the demo document using NLP pipeline."""
    if document_id and segments:
        print(f"Extracting insights from demo document (ID: {document_id})...")
        
        # Initialize NLP pipeline
        nlp_pipeline = NLPLlmPipeline()
        
        # Extract text from segments
        segment_texts = [segment["text"] for segment in segments]
        
        # Combine for full document text
        full_document_text = "\n\n".join(segment_texts)
        
        # Process with NLP pipeline
        metadata = {
            "company": "Demo Corp",
            "filing_date": datetime.datetime.now().isoformat(),
            "doc_type": "10-K"
        }
        
        # Use specific queries to extract insights
        queries = ["Total Revenue", "Net Income", "EPS", "Operating Profit", "Debt to Equity Ratio"]
        
        # Process document (if OPENAI_API_KEY is set)
        if nlp_pipeline.llm:
            insights = nlp_pipeline.process_document(
                document_text=full_document_text,
                document_id=document_id,
                metadata=metadata,
                queries=queries
            )
            
            # Save insights to database
            save_insights(document_id, insights)
            print("Demo insights extracted and saved.")
        else:
            print("OpenAI API key not set. Using mock insights instead.")
            mock_insights = generate_mock_insights(document_id)
            save_insights(document_id, mock_insights)
            print("Mock insights generated and saved.")
    else:
        print("Cannot extract insights: No document ID or segments provided.")

def generate_mock_insights(document_id):
    """Generate mock insights when API key is not available."""
    return {
        "document_id": document_id,
        "company": "Demo Corp",
        "processing_time": 2.5,
        "model_version": "mock-model",
        "timestamp": datetime.datetime.now().isoformat(),
        "extracted_metrics": {
            "Total Revenue": "$1.5 billion",
            "Net Income": "$320 million",
            "EPS": "$3.45",
            "Operating Profit": "$550 million",
            "Debt to Equity Ratio": "0.4"
        },
        "sentiment": "Positive: The document indicates strong financial performance with significant growth in revenue and net income.",
        "risks": "Market competition, regulatory changes, currency fluctuations, trade tensions, and rising interest rates.",
        "summary": "Demo Corp reported strong financial results with 15% revenue growth reaching $1.5 billion and 20% increase in net income to $320 million. EPS was $3.45."
    }

def save_insights(document_id, insights):
    """Save insights to the database."""
    try:
        # Save metrics
        for metric_name, metric_value in insights.get("extracted_metrics", {}).items():
            insight_data = {
                "metric": metric_name,
                "value": metric_value,
                "timestamp": datetime.datetime.now(),
                "company": "Demo Corp",
                "source_reference": f"document_id={document_id}, type=metric",
                "model_version": insights.get("model_version", "unknown"),
                "original_text": "",
                "page_numbers": []
            }
            storage.save_insight(insight_data)
            
        # Save sentiment analysis
        if "sentiment" in insights:
            insight_data = {
                "metric": "sentiment",
                "value": insights["sentiment"],
                "timestamp": datetime.datetime.now(),
                "company": "Demo Corp",
                "source_reference": f"document_id={document_id}, type=sentiment",
                "model_version": insights.get("model_version", "unknown"),
                "original_text": "",
                "page_numbers": []
            }
            storage.save_insight(insight_data)
            
        # Save risk identification
        if "risks" in insights:
            insight_data = {
                "metric": "risks",
                "value": insights["risks"],
                "timestamp": datetime.datetime.now(),
                "company": "Demo Corp",
                "source_reference": f"document_id={document_id}, type=risks",
                "model_version": insights.get("model_version", "unknown"),
                "original_text": "",
                "page_numbers": []
            }
            storage.save_insight(insight_data)
            
        # Save summary
        if "summary" in insights:
            insight_data = {
                "metric": "summary",
                "value": insights["summary"],
                "timestamp": datetime.datetime.now(),
                "company": "Demo Corp",
                "source_reference": f"document_id={document_id}, type=summary",
                "model_version": insights.get("model_version", "unknown"),
                "original_text": "",
                "page_numbers": []
            }
            storage.save_insight(insight_data)
            
        print("Insights saved successfully.")
    except Exception as e:
        print(f"Error saving insights: {e}")

def create_env_file():
    """Create a template .env file if it doesn't exist."""
    env_path = ".env"
    if not os.path.exists(env_path):
        print("Creating template .env file...")
        with open(env_path, 'w') as f:
            f.write("# Database configuration\n")
            f.write(f"DB_HOST={MONGO_CONFIG['host']}\n")
            f.write(f"DB_NAME={MONGO_CONFIG['database']}\n")
            f.write(f"DB_USER={MONGO_CONFIG['user']}\n")
            f.write(f"DB_PASSWORD={MONGO_CONFIG['password']}\n")
            f.write("\n# API configuration\n")
            f.write("API_HOST=0.0.0.0\n")
            f.write("API_PORT=8000\n")
            f.write("API_DEBUG=False\n")
            f.write("API_KEY=default_api_key_change_me\n")
            f.write("CORS_ORIGINS=*\n")
            f.write("\n# LLM configuration\n")
            f.write("OPENAI_API_KEY=\n")
            f.write("LLM_MODEL_NAME=gpt-3.5-turbo\n")
            f.write("LLM_TEMPERATURE=0.7\n")
            f.write("\n# File storage configuration\n")
            f.write(f"TEMP_FILE_DIR={MONGO_CONFIG['temp_dir']}\n")
            f.write(f"MAX_UPLOAD_SIZE={MONGO_CONFIG['max_upload_size']}\n")
        print(f".env file created at {os.path.abspath(env_path)}")
    else:
        print(".env file already exists.")

def setup_project_folders():
    """Create necessary project folders if they don't exist."""
    folders = [
        "logs",
        "logs/predictions",
        "logs/corrections",
        "logs/feedback",
        "temp_files",
        "faiss_index"
    ]
    
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"Created folder: {folder}")
        else:
            print(f"Folder already exists: {folder}")

def main():
    parser = argparse.ArgumentParser(description='Set up Financial Document Intelligence System')
    parser.add_argument('--skip-demo', action='store_true', help='Skip creating demo data')
    parser.add_argument('--force-init-db', action='store_true', help='Force initialize database tables')
    args = parser.parse_args()
    
    # Set up project folders
    setup_project_folders()
    
    # Create template .env file
    create_env_file()
    
    # Initialize database schema
    if args.force_init_db:
        initialize_database()
    
    if not args.skip_demo:
        # Create demo document
        document_id, segments = create_demo_document()
        
        # Extract insights
        extract_insights(document_id, segments)

if __name__ == "__main__":
    main()