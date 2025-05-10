import unittest
from unittest.mock import patch, MagicMock
import sys
import os
from bson.objectid import ObjectId

# Add project root to path to allow imports from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.storage_access import storage
from src.config import MONGO_CONFIG

class TestStorage(unittest.TestCase):
    def setUp(self):
        # Create the patch for pymongo
        self.pymongo_patcher = patch('src.storage_access.storage.pymongo')
        self.mock_pymongo = self.pymongo_patcher.start()

        # Reset storage state
        storage.client = None
        storage.db = None
        
        # Set up mock client and database
        self.mock_client = MagicMock()
        self.mock_db = MagicMock()
        self.mock_pymongo.MongoClient.return_value = self.mock_client
        self.mock_client.__getitem__.return_value = self.mock_db

        # Set up mock collections
        self.mock_documents = MagicMock()
        self.mock_segments = MagicMock()
        self.mock_insights = MagicMock()
        self.mock_db.documents = self.mock_documents
        self.mock_db.segments = self.mock_segments
        self.mock_db.insights = self.mock_insights

        # Setup default empty collections list
        self.mock_db.list_collection_names.return_value = []
        
    def tearDown(self):
        self.pymongo_patcher.stop()
        storage.client = None
        storage.db = None

    def test_connect_to_mongo(self):
        # Call connect_to_mongo
        storage.connect_to_mongo()
        # Check the MongoDB client was created with correct URI
        self.mock_pymongo.MongoClient.assert_called_once_with(MONGO_CONFIG["uri"])
        # Check the database was selected
        self.mock_client.__getitem__.assert_called_once_with(MONGO_CONFIG["database_name"])
        # Check storage.client and storage.db were set
        self.assertEqual(storage.client, self.mock_client)
        self.assertEqual(storage.db, self.mock_db)

    def test_initialize_database(self):
        # Call initialize_database
        storage.initialize_database()
        # Check collections were created
        self.mock_db.create_collection.assert_any_call("documents")
        self.mock_db.create_collection.assert_any_call("segments")
        self.mock_db.create_collection.assert_any_call("insights")
        # Check indexes were created
        self.mock_documents.create_index.assert_called_once()
        self.mock_insights.create_index.assert_called_once()

    def test_save_document(self):
        doc_data = {"company": "TestCorp", "doc_type": "10-K"}
        mock_result = MagicMock()
        mock_result.inserted_id = ObjectId()
        self.mock_documents.insert_one.return_value = mock_result

        doc_id = storage.save_document(doc_data)

        self.mock_documents.insert_one.assert_called_once_with(doc_data)
        self.assertEqual(doc_id, str(mock_result.inserted_id))

    def test_get_document_by_id(self):
        doc_id = str(ObjectId())
        expected_doc = {"_id": ObjectId(doc_id), "company": "TestCorp"}
        self.mock_documents.find_one.return_value = expected_doc

        result = storage.get_document_by_id(doc_id)

        self.mock_documents.find_one.assert_called_once_with({"_id": ObjectId(doc_id)})
        self.assertEqual(result, expected_doc)

    def test_save_segments(self):
        doc_id = str(ObjectId())
        segments = [{"text": "segment1"}, {"text": "segment2"}]
        expected_segments = [
            {"text": "segment1", "document_id": ObjectId(doc_id)},
            {"text": "segment2", "document_id": ObjectId(doc_id)}
        ]
        mock_result = MagicMock()
        mock_result.inserted_ids = [ObjectId(), ObjectId()]
        self.mock_segments.insert_many.return_value = mock_result

        storage.save_segments(segments, doc_id)

        self.mock_segments.insert_many.assert_called_once_with(expected_segments)

    def test_get_document_segments(self):
        doc_id = str(ObjectId())
        expected_segments = [{"text": "segment1", "document_id": ObjectId(doc_id)}]
        self.mock_segments.find.return_value = expected_segments

        result = storage.get_document_segments(doc_id)

        self.mock_segments.find.assert_called_once_with({"document_id": ObjectId(doc_id)})
        self.assertEqual(result, expected_segments)

    def test_save_insight(self):
        doc_id = str(ObjectId())
        insight_data = {"metric": "Revenue", "value": "1M", "document_id": doc_id}
        expected_data = insight_data.copy()
        expected_data["document_id"] = ObjectId(doc_id)
        mock_result = MagicMock()
        mock_result.inserted_id = ObjectId()
        self.mock_insights.insert_one.return_value = mock_result

        result = storage.save_insight(insight_data)

        self.mock_insights.insert_one.assert_called_once_with(expected_data)
        self.assertEqual(result, str(mock_result.inserted_id))

    def test_query_insights(self):
        doc_id = str(ObjectId())
        metric = "Revenue"
        expected_query = {
            "document_id": ObjectId(doc_id),
            "metric_name": metric
        }
        expected_insights = [{"metric": metric, "value": "1M"}]
        self.mock_insights.find.return_value = expected_insights

        result = storage.query_insights(document_id=doc_id, metric=metric)

        self.mock_insights.find.assert_called_once_with(expected_query)
        self.assertEqual(result, expected_insights)

    def test_get_all_insights(self):
        expected_insights = [
            {"metric": "Revenue", "value": "1M"},
            {"metric": "Profit", "value": "100K"}
        ]
        self.mock_insights.find.return_value = expected_insights

        result = storage.get_all_insights()

        self.mock_insights.find.assert_called_once_with()
        self.assertEqual(result, expected_insights)

if __name__ == '__main__':
    unittest.main()
