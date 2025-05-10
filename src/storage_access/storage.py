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
    global client, db
    try:
        client = pymongo.MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        logger.info(f"Successfully connected to MongoDB at {MONGO_URI} and database '{DATABASE_NAME}'")
        # Create collections if they don't exist and add any necessary indexes
        initialize_database()
    except pymongo.errors.ConnectionFailure as e:
        logger.error(f"Could not connect to MongoDB: {e}")
        sys.exit(1)

connect_to_mongo() # Initialize connection when module is loaded

def get_db():
    """Returns the MongoDB database instance."""
    if db is None:
        connect_to_mongo()
    return db

def initialize_database():
    """Creates collections and indexes if they don't already exist."""
    db_instance = get_db()
    collections = ["documents", "segments", "insights"]
    for collection_name in collections:
        if collection_name not in db_instance.list_collection_names():
            db_instance.create_collection(collection_name)
            logger.info(f"Created collection: {collection_name}")

    # Example of creating an index (adjust as needed)
    if "documents" in db_instance.list_collection_names():
        db_instance.documents.create_index([("company", pymongo.ASCENDING), ("doc_type", pymongo.ASCENDING)], background=True)
        logger.info("Created index on documents collection (company, doc_type)")
    if "insights" in db_instance.list_collection_names():
        db_instance.insights.create_index([("document_id", pymongo.ASCENDING), ("metric_name", pymongo.ASCENDING)], background=True)
        logger.info("Created index on insights collection (document_id, metric_name)")

def save_document(document_data: dict) -> str:
    """Saves document metadata to the 'documents' collection.
    Returns the ID of the inserted document.
    """
    db_instance = get_db()
    result = db_instance.documents.insert_one(document_data)
    logger.info(f"Saved document with ID: {result.inserted_id}")
    return str(result.inserted_id)

def save_segments(segments: list, document_id: str):
    """Saves document segments to the 'segments' collection.
    Each segment should have a 'document_id' field linking it to the parent document.
    """
    db_instance = get_db()
    if not segments:
        logger.info("No segments to save.")
        return
    for segment in segments:
        segment["document_id"] = ObjectId(document_id) # Ensure document_id is ObjectId if it's a string
    result = db_instance.segments.insert_many(segments)
    logger.info(f"Saved {len(result.inserted_ids)} segments for document ID: {document_id}")

def save_insight(insight_data: dict) -> str:
    """Saves an insight to the 'insights' collection.
    Returns the ID of the inserted insight.
    """
    db_instance = get_db()
    if "document_id" in insight_data and isinstance(insight_data["document_id"], str):
        insight_data["document_id"] = ObjectId(insight_data["document_id"])
    result = db_instance.insights.insert_one(insight_data)
    logger.info(f"Saved insight with ID: {result.inserted_id}")
    return str(result.inserted_id)

def get_all_insights() -> list:
    """Retrieves all insights from the 'insights' collection."""
    db_instance = get_db()
    insights = list(db_instance.insights.find())
    logger.info(f"Retrieved {len(insights)} insights.")
    return insights

def get_document_by_id(document_id: str) -> dict:
    """Retrieves a document by its ID from the 'documents' collection."""
    db_instance = get_db()
    document = db_instance.documents.find_one({"_id": ObjectId(document_id)})
    if document:
        logger.info(f"Retrieved document with ID: {document_id}")
    else:
        logger.warning(f"No document found with ID: {document_id}")
    return document

def get_document_segments(document_id: str) -> list:
    """Retrieves all segments for a given document ID from the 'segments' collection."""
    db_instance = get_db()
    segments = list(db_instance.segments.find({"document_id": ObjectId(document_id)}))
    logger.info(f"Retrieved {len(segments)} segments for document ID: {document_id}")
    return segments

def query_insights(metric: str = None, date_str: str = None, company: str = None, document_id: str = None) -> list:
    """Queries insights based on metric, date, company, or document_id."""
    db_instance = get_db()
    query = {}
    if metric:
        query["metric_name"] = metric # Assuming insights have a 'metric_name' field
    if date_str: # Assuming insights have a 'date' field (e.g., as string or datetime object)
        # This is a simple exact match. You might need more complex date range queries.
        query["date"] = date_str
    if company: # Assuming insights are linked to documents that have a 'company' field
                # This might require a join or a denormalized company field in insights
        # For a simple approach, if insights store company directly:
        # query["company"] = company
        # If company is in the document, you might need to query documents first then insights
        logger.warning("Querying insights by company might require specific schema design.")
    if document_id:
        query["document_id"] = ObjectId(document_id)

    insights = list(db_instance.insights.find(query))
    logger.info(f"Retrieved {len(insights)} insights based on query: {query}")
    return insights

def get_insights_by_document(document_id: str) -> list:
    """Retrieves all insights for a given document ID."""
    return query_insights(document_id=document_id)

# Example of how to clear a collection (use with caution)
def _clear_collection(collection_name: str):
    db_instance = get_db()
    if collection_name in db_instance.list_collection_names():
        db_instance[collection_name].delete_many({})
        logger.info(f"Cleared all documents from collection: {collection_name}")

if __name__ == '__main__':
    # This block can be used for testing the storage module directly
    logger.info("Running storage module tests...")
    connect_to_mongo() # Ensure connection
    initialize_database() # Ensure collections and indexes

    # Example usage:
    # 1. Clear existing data for a clean test
    _clear_collection("documents")
    _clear_collection("segments")
    _clear_collection("insights")

    # 2. Save a document
    sample_doc_data = {
        "company": "TestCorp Inc.",
        "doc_type": "10-K",
        "filing_date": "2025-01-15",
        "source_url": "http://example.com/10k",
        "processed": False
    }
    doc_id = save_document(sample_doc_data)
    print(f"Saved document with ID: {doc_id}")

    # 3. Retrieve the document
    retrieved_doc = get_document_by_id(doc_id)
    print(f"Retrieved document: {retrieved_doc}")

    # 4. Save segments for the document
    sample_segments = [
        {"text": "This is the first segment.", "page_number": 1, "segment_type": "introduction"},
        {"text": "This is the second segment, discussing financials.", "page_number": 5, "segment_type": "financials"}
    ]
    save_segments(sample_segments, doc_id)

    # 5. Retrieve segments
    retrieved_segments = get_document_segments(doc_id)
    print(f"Retrieved segments: {retrieved_segments}")

    # 6. Save an insight
    sample_insight_data = {
        "document_id": doc_id,
        "metric_name": "Total Revenue",
        "value": "100M USD",
        "source_text": "Total revenue was 100 million US dollars.",
        "page_number": 5,
        "date": "2025-01-15"
    }
    insight_id = save_insight(sample_insight_data)
    print(f"Saved insight with ID: {insight_id}")

    # 7. Query insights
    queried_insights = query_insights(metric="Total Revenue", document_id=doc_id)
    print(f"Queried insights: {queried_insights}")

    all_insights_for_doc = get_insights_by_document(doc_id)
    print(f"All insights for document {doc_id}: {all_insights_for_doc}")

    all_insights = get_all_insights()
    print(f"All insights in DB: {len(all_insights)}")

    logger.info("Storage module tests completed.")