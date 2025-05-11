import unittest
import sys
import os
import tempfile
import shutil

# Add project root to path to allow imports from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.document_processor.processor import DocumentProcessor

class TestEndToEnd(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.processor = DocumentProcessor()
        self.pdf_path = os.path.abspath("test_doc.pdf")
        
    def test_full_process(self):
        """Test the full document processing workflow end-to-end"""
        print(f"\nTesting full process on file: {self.pdf_path}")
        self.assertTrue(os.path.exists(self.pdf_path), f"Test file not found: {self.pdf_path}")
        
        # Step 1: Load document
        print("1. Loading document...")
        content = self.processor.load_document(self.pdf_path)
        self.assertIsNotNone(content)
        self.assertIsInstance(content, str)
        self.assertTrue(len(content) > 0)
        print(f"   - Document loaded: {len(content)} characters")
        
        # Step 2: Clean text
        print("2. Cleaning text...")
        cleaned = self.processor.clean_text(content)
        self.assertIsNotNone(cleaned)
        self.assertIsInstance(cleaned, str)
        self.assertTrue(len(cleaned) > 0)
        print(f"   - Text cleaned: {len(cleaned)} characters")
        
        # Step 3: Segment document
        print("3. Segmenting document...")
        segments = self.processor.segment_document(cleaned)
        self.assertIsNotNone(segments)
        self.assertIsInstance(segments, list)
        print(f"   - Document segmented into {len(segments)} parts")
        
        # Check segment structure
        if segments:
            segment = segments[0]
            self.assertIn('section_type', segment)
            self.assertIn('text', segment)
            self.assertIn('start_page', segment)
            self.assertIn('end_page', segment)
            print(f"   - First segment type: {segment['section_type']}")
        
        # Step 4: Extract tables
        print("4. Extracting tables...")
        tables = self.processor.extract_tables(cleaned)
        self.assertIsNotNone(tables)
        self.assertIsInstance(tables, list)
        print(f"   - Found {len(tables)} tables")
        
        print("\nAll tests passed successfully!")

if __name__ == '__main__':
    unittest.main()
