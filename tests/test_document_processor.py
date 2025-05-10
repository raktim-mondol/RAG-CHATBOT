import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import tempfile
import shutil

# Add project root to path to allow imports from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.document_processor.processor import DocumentProcessor

class TestDocumentProcessor(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.processor = DocumentProcessor()
        self.test_text_content = "Test plain text content"
        
        # Use dummy.pdf from project root
        self.pdf_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dummy.pdf")
        
        # Create temporary test files
        self.temp_dir = tempfile.mkdtemp()
        self.txt_path = os.path.join(self.temp_dir, "test.txt")
        
        # Create test text file
        with open(self.txt_path, 'w') as f:
            f.write(self.test_text_content)
            
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir)
        
    def test_load_pdf_document(self):
        """Test loading PDF document"""
        result = self.processor.load_document(self.pdf_path)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)
        
    def test_load_text_document(self):
        """Test loading text document"""
        result = self.processor.load_document(self.txt_path)
        self.assertIsNotNone(result)
        self.assertEqual(result, self.test_text_content)
        
    def test_segment_document(self):
        """Test document segmentation"""
        test_content = """
        # Executive Summary
        Summary content here.
        
        # Risk Factors
        Risk content here.
        
        # Financial Data
        Financial metrics here.
        """
        
        segments = self.processor.segment_document(test_content)
        self.assertIsInstance(segments, list)
        self.assertTrue(len(segments) > 0)
        
        # Check segment structure
        for segment in segments:
            self.assertIn('section_type', segment)
            self.assertIn('text', segment)
            self.assertIn('start_page', segment)
            self.assertIn('end_page', segment)
            
    def test_clean_text(self):
        """Test text cleaning functionality"""
        test_text = """
        Revenue: $1,234,567.89
        Date: 2024-12-31
        Some random text with  multiple   spaces
        """
        
        cleaned_text = self.processor.clean_text(test_text)
        self.assertIsInstance(cleaned_text, str)
        self.assertNotIn("  ", cleaned_text)  # No double spaces
        
    def test_extract_tables(self):
        """Test table extraction"""
        test_content = """
        | Metric | Value |
        |---------|-------|
        | Revenue | $100M |
        | Profit | $20M |
        """
        
        tables = self.processor.extract_tables(test_content)
        self.assertIsInstance(tables, list)
        
    def test_error_handling(self):
        """Test error handling for invalid files"""
        with self.assertRaises(Exception):
            self.processor.load_document("nonexistent_file.pdf")
            
if __name__ == '__main__':
    unittest.main()
