# Financial Document Intelligence System

A comprehensive system for processing, analyzing, and extracting insights from financial documents using NLP and LLM technologies.

## Overview

The Financial Document Intelligence System is designed to automatically process financial documents (10-K, 10-Q, earnings calls, etc.), extract key metrics, identify risks, analyze sentiment, and generate summaries. It uses a modular architecture with specialized components for document ingestion, storage, NLP processing, and monitoring.

## Features

- **Document Ingestion Pipeline**: Upload and process financial documents from various sources (PDF, HTML, text)
- **Financial NLP Processing**: Extract key metrics, identify risks, analyze sentiment, and generate summaries
- **Retrieval-Augmented Generation (RAG)**: Contextualize and enhance LLM analyses by retrieving relevant document sections
- **API**: REST endpoints for document upload, processing, and insight retrieval
- **Storage**: Persistent storage for documents, document segments, and extracted insights
- **Monitoring**: Track model performance and collect human feedback for continuous improvement

## Architecture

The system consists of several key components:

1. **API Layer**: FastAPI-based REST API for client interaction
2. **Storage Layer**: MongoDB database for storing documents, segments, and insights
3. **Ingestion Pipeline**: Process and segment raw financial documents
4. **NLP/LLM Pipeline**: Extract insights using various NLP/LLM components
5. **Monitoring & Feedback**: Track model performance and collect human feedback

## Getting Started

### Prerequisites

- Python 3.9+
- MongoDB
- Docker and Docker Compose (optional)

### Installation

#### Using Docker (Recommended)

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/financial-document-intelligence.git
   cd financial-document-intelligence
   ```

2. Create a `.env` file with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   API_KEY=your_custom_api_key_for_authentication
   ```

3. Build and start the containers:
   ```
   docker-compose up -d --build
   ```

4. The API will be available at http://localhost:8000

#### Manual Installation

1. Clone this repository and navigate to the directory:
   ```
   git clone https://github.com/yourusername/financial-document-intelligence.git
   cd financial-document-intelligence
   ```

2. Create a virtual environment and install dependencies:
   ```
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Run the setup script to initialize the environment:
   ```
   python setup.py
   ```

4. Update the `.env` file with your configuration settings.

5. Initialize the database:
   ```
   python setup.py --force-init-db
   ```

6. Create a demo document (optional):
   ```
   python setup.py
   ```

7. Start the API server:
   ```
   uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
   ```

## Usage

### API Endpoints

- **GET /** - API health check
- **GET /health** - System health check
- **POST /upload-document/** - Upload a document for processing
- **POST /analyze-document/{document_id}** - Analyze a previously uploaded document
- **GET /insights/** - Retrieve all insights (paginated)
- **GET /insights/query/** - Query insights by metric, date, or company
- **GET /documents/** - Retrieve all documents (paginated)
- **GET /documents/{document_id}** - Retrieve a specific document with its segments and insights

### Example: Upload and Process a Document

```python
import requests

# API base URL
api_url = "http://localhost:8000"
api_key = "your_api_key_here"  # Use the API_KEY from your .env file

# Upload a document
files = {'file': open('path/to/financial_document.pdf', 'rb')}
data = {'doc_type': '10-K', 'company': 'Example Corp'}
response = requests.post(
    f"{api_url}/upload-document/",
    files=files,
    data=data,
    params={'api_key': api_key}
)
print(response.json())

# The document will be processed in the background.
# You can check the results later using the document ID.

# Get document insights
document_id = response.json().get('document_id')
response = requests.get(
    f"{api_url}/documents/{document_id}",
    params={'api_key': api_key}
)
print(response.json())
```

## Configuration

Configuration is managed through environment variables, which can be set in the `.env` file:

- **Database Configuration**: `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- **API Configuration**: `API_HOST`, `API_PORT`, `API_DEBUG`, `API_KEY`, `CORS_ORIGINS`
- **LLM Configuration**: `OPENAI_API_KEY`, `LLM_MODEL_NAME`, `LLM_TEMPERATURE`
- **File Storage**: `TEMP_FILE_DIR`, `MAX_UPLOAD_SIZE`
- **Embedding Model**: `EMBEDDING_MODEL`, `FAISS_INDEX_PATH`
- **Logging**: `LOGGING_LEVEL`, `LOGGING_FORMAT`

## Development

### Project Structure

```
financial-document-intelligence/
├── docs/                    # Documentation files
├── src/                     # Source code
│   ├── api/                 # API endpoints
│   ├── ingestion_pipeline/  # Document ingestion components
│   ├── nlp_llm_pipeline/    # NLP processing components
│   ├── monitoring_feedback/ # Monitoring and feedback components
│   ├── storage_access/      # Database access components
│   └── config.py            # Centralized configuration
├── logs/                    # Log files
│   ├── predictions/         # Model prediction logs
│   ├── corrections/         # Human correction logs
│   └── feedback/            # User feedback logs
├── temp_files/              # Temporary file storage
├── faiss_index/             # Vector index storage
├── docker-compose.yml       # Docker Compose configuration
├── Dockerfile               # Docker configuration
├── requirements.txt         # Python dependencies
├── setup.py                 # Setup script
└── README.md                # This file
```

### Adding New Components

To add a new NLP component:

1. Create a new module in `src/nlp_llm_pipeline/`
2. Implement the component with a clear interface
3. Update the main pipeline in `src/nlp_llm_pipeline/pipeline.py`
4. Add any new configuration parameters to `src/config.py`

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI for GPT models
- LangChain for RAG components
- FAISS for vector similarity search
- ProsusAI for FinBERT financial embedding model