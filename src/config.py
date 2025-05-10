import os
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# Database configuration
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "database": os.environ.get("DB_NAME", "financial_intelligence"),
    "user": os.environ.get("DB_USER", "user"),
    "password": os.environ.get("DB_PASSWORD", "password"),
}

# API configuration
API_CONFIG = {
    "host": os.environ.get("API_HOST", "0.0.0.0"),
    "port": int(os.environ.get("API_PORT", 8000)),
    "debug": os.environ.get("API_DEBUG", "False").lower() == "true",
    "api_key": os.environ.get("API_KEY", "default_api_key_change_me"),
    "cors_origins": os.environ.get("CORS_ORIGINS", "*").split(","),
}

# LLM configuration
LLM_CONFIG = {
    "api_key": os.environ.get("OPENAI_API_KEY", ""),
    "model": os.environ.get("LLM_MODEL_NAME", "gpt-4o-mini"),  # Changed from model_name to model
    "temperature": float(os.environ.get("LLM_TEMPERATURE", "0.7")),
}

# File storage configuration
FILE_STORAGE = {
    "temp_dir": os.environ.get("TEMP_FILE_DIR", "temp_files"),
    "max_upload_size": int(os.environ.get("MAX_UPLOAD_SIZE", 10 * 1024 * 1024)),  # 10MB default
}

# Create temp directory if it doesn't exist
if not os.path.exists(FILE_STORAGE["temp_dir"]):
    os.makedirs(FILE_STORAGE["temp_dir"])

# Embedding model configuration
EMBEDDING_CONFIG = {
    "model_name": os.environ.get("EMBEDDING_MODEL", "ProsusAI/finbert"),
    "index_path": os.environ.get("FAISS_INDEX_PATH", "faiss_index"),
}

# Logging configuration
LOGGING_CONFIG = {
    "level": os.environ.get("LOGGING_LEVEL", "INFO"),
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
}