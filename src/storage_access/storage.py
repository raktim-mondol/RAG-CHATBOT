import pymongo
import logging
import sys
import os
from bson.objectid import ObjectId

# Add project root to path to allow imports from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.config import MONGO_CONFIG

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection details from config
MONGO_URI = MONGO_CONFIG["uri"]
DATABASE_NAME = MONGO_CONFIG["database_name"]

client = None
db = None

def connect_to_mongo():
    """Connect to MongoDB and set up the client."""
    global client, db
    if client is None:
        client = pymongo.MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        logger.info(f"Successfully connected to MongoDB at {MONGO_URI} and database '{DATABASE_NAME}'")
    return db

def get_db():
    """Get MongoDB database instance, connecting if necessary."""
    global db
    if db is None:
        db = connect_to_mongo()
    return db

def initialize_database():
    """Initialize the database with required collections and indexes."""
    db_instance = get_db()

    # Create collections if they don't exist
    if "documents" not in db_instance.list_collection_names():
        db_instance.create_collection("documents")
        logger.info("Created collection: documents")

    if "segments" not in db_instance.list_collection_names():
        db_instance.create_collection("segments")
        logger.info("Created collection: segments")

    if "insights" not in db_instance.list_collection_names():
        db_instance.create_collection("insights")
        logger.info("Created collection: insights")

    # Create indexes
    db_instance.documents.create_index([("company", pymongo.ASCENDING), ("doc_type", pymongo.ASCENDING)])
    logger.info("Created index on documents collection (company, doc_type)")

    db_instance.insights.create_index([("document_id", pymongo.ASCENDING), ("metric_name", pymongo.ASCENDING)])
    logger.info("Created index on insights collection (document_id, metric_name)")

def save_document(doc_data):
    """Save a document to the database."""
    db_instance = get_db()
    result = db_instance.documents.insert_one(doc_data)
    doc_id = str(result.inserted_id)
    logger.info(f"Saved document with ID: {doc_id}")
    return doc_id

def get_document_by_id(document_id):
    """Retrieve a document by its ID."""
    db_instance = get_db()
    doc = db_instance.documents.find_one({"_id": ObjectId(document_id)})
    if doc:
        logger.info(f"Retrieved document with ID: {document_id}")
    else:
        logger.info(f"No document found with ID: {document_id}")
    return doc

def save_segments(segments_data, document_id):
    """Save document segments to the database."""
    db_instance = get_db()
    segments_to_insert = []
    for segment in segments_data:
        segment["document_id"] = ObjectId(document_id)
        segments_to_insert.append(segment)
    
    result = db_instance.segments.insert_many(segments_to_insert)
    logger.info(f"Saved {len(result.inserted_ids)} segments for document ID: {document_id}")
    return result.inserted_ids

def get_document_segments(document_id):
    """Retrieve segments for a document."""
    db_instance = get_db()
    segments = list(db_instance.segments.find({"document_id": ObjectId(document_id)}))
    logger.info(f"Retrieved {len(segments)} segments for document ID: {document_id}")
    return segments

def save_insight(insight_data):
    """Save an insight to the database."""
    db_instance = get_db()
    if "document_id" in insight_data:
        insight_data["document_id"] = ObjectId(insight_data["document_id"])
    result = db_instance.insights.insert_one(insight_data)
    insight_id = str(result.inserted_id)
    logger.info(f"Saved insight with ID: {insight_id}")
    return insight_id

def query_insights(document_id=None, metric=None):
    """Query insights based on document ID and/or metric."""
    db_instance = get_db()
    query = {}
    if document_id:
        query["document_id"] = ObjectId(document_id)
    if metric:
        query["metric_name"] = metric
    insights = list(db_instance.insights.find(query))
    logger.info(f"Retrieved {len(insights)} insights based on query: {query}")
    return insights

def get_all_insights():
    """Retrieve all insights from the database."""
    db_instance = get_db()
    insights = list(db_instance.insights.find())
    logger.info(f"Retrieved {len(insights)} insights.")
    return insights