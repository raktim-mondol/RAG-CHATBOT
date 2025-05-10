# src/ingestion_pipeline/ingest.py

import requests
from bs4 import BeautifulSoup
import pdfminer.high_level # For PDF parsing
import fitz # PyMuPDF
import logging
import os
import sys
import tempfile
import re
import datetime
from typing import List, Dict, Any

# Add project root to path to allow imports from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.config import FILE_STORAGE, LOGGING_CONFIG, MONGO_CONFIG # Added MONGO_CONFIG
from src.storage_access import storage

# Configure logging
logging.basicConfig(level=getattr(logging, LOGGING_CONFIG["level"]), 
                   format=LOGGING_CONFIG["format"])

class IngestionPipeline:
    def __init__(self):
        """Initializes the Ingestion Pipeline."""
        logging.info("Ingestion Pipeline initialized.")
        # Create temp directory if it doesn't exist
        if not os.path.exists(FILE_STORAGE["temp_dir"]):
            os.makedirs(FILE_STORAGE["temp_dir"])

    def acquire_document(self, source_url: str, doc_type: str):
        """Acquires a document from a given source URL."""
        logging.info(f"Attempting to acquire document from: {source_url}")
        try:
            response = requests.get(source_url, stream=True)
            response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)

            # Determine file format (basic implementation, can be improved)
            content_type = response.headers.get('content-type', '').lower()
            if 'pdf' in content_type:
                doc_format = 'pdf'
                file_extension = '.pdf'
            elif 'html' in content_type:
                doc_format = 'html'
                file_extension = '.html'
            elif 'text/plain' in content_type:
                doc_format = 'text'
                file_extension = '.txt'
            else:
                # Default to binary or handle other formats
                doc_format = 'binary'
                file_extension = '.bin' # Or try to infer from URL

            # Use tempfile to create a secure temporary file
            try:
                temp_file_path = os.path.join(FILE_STORAGE["temp_dir"], f"ingestion_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}{file_extension}")
                
                with open(temp_file_path, 'wb') as temp_file:
                    for chunk in response.iter_content(chunk_size=8192):
                        temp_file.write(chunk)
                    
                logging.info(f"Created temporary file for download: {temp_file_path}")

            except IOError as e:
                logging.error(f"Error creating or writing to temporary file: {e}")
                return None, None

            logging.info(f"Successfully acquired and saved document to: {temp_file_path}")
            return temp_file_path, doc_format

        except requests.exceptions.RequestException as e:
            logging.error(f"Error acquiring document from {source_url}: {e}")
            return None, None

    def parse_document(self, file_path: str, doc_format: str):
        """Parses a document and extracts raw text."""
        logging.info(f"Parsing document: {file_path} (Format: {doc_format})")
        raw_text = ""
        try:
            if doc_format == 'pdf':
                try:
                    raw_text = pdfminer.high_level.extract_text(file_path)
                    logging.info("PDF parsing completed using PDFMiner.six.")
                except Exception as pdfminer_e:
                    logging.warning(f"PDFMiner.six failed to parse {file_path}: {pdfminer_e}. Attempting with PyMuPDF.")
                    try:
                        doc = fitz.open(file_path)
                        raw_text = ""
                        for page in doc:
                            raw_text += page.get_text()
                        logging.info("PDF parsing completed using PyMuPDF.")
                    except Exception as pymupdf_e:
                        logging.error(f"PyMuPDF also failed to parse {file_path}: {pymupdf_e}")
                        return None
            elif doc_format == 'html':
                with open(file_path, 'r', encoding='utf-8') as f:
                    soup = BeautifulSoup(f, 'html.parser')
                    raw_text = soup.get_text()
                logging.info("HTML parsing completed.")
            elif doc_format == 'text':
                with open(file_path, 'r', encoding='utf-8') as f:
                    raw_text = f.read()
                logging.info("Plain text parsing completed.")
            else:
                logging.warning(f"Unsupported document format for parsing: {doc_format}")
                return None

            return raw_text

        except FileNotFoundError:
            logging.error(f"Error parsing document {file_path}: File not found.")
            return None
        except IOError as e:
            logging.error(f"Error reading document {file_path}: {e}")
            return None
        except Exception as e:
            # Catch any other unexpected errors during parsing
            logging.error(f"An unexpected error occurred while parsing document {file_path}: {e}")
            return None

    def clean_text(self, text: str) -> str:
        """Cleans and normalizes text."""
        logging.info("Cleaning text...")
        if not text:
            return ""
            
        # Remove extra whitespace, normalize case, handle special characters, etc.
        cleaned_text = text.strip()
        # Example: Replace multiple newlines with a single one
        cleaned_text = re.sub(r'\n+', '\n', cleaned_text)
        # Example: Remove excessive spaces
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
        logging.info("Text cleaning completed.")
        return cleaned_text

    def handle_structured_content(self, file_path: str, doc_format: str) -> dict:
        """
        Handles structured content like tables and formulas, converting them to JSON.
        This is a placeholder and requires dedicated libraries/logic for different formats.
        """
        logging.info(f"Handling structured content for {file_path} (Format: {doc_format})...")
        structured_data = {}

        # In future, implement table extraction using libraries like camelot-py or tabula-py
        if doc_format == 'pdf':
            logging.warning("PDF table extraction is a placeholder and not implemented.")
            # Structured data would be extracted here
        elif doc_format == 'html':
            logging.warning("HTML table extraction is a placeholder and not implemented.")
            # HTML tables would be extracted here

        logging.info("Structured content handling completed (placeholder).")
        return structured_data

    def segment_document(self, raw_text: str, doc_type: str):
        """Segments the raw text into logical sections based on document type."""
        logging.info(f"Segmenting document of type: {doc_type}...")

        segments = []

        if doc_type in ["10-K", "10-Q"]:
            # Basic rule-based approach for SEC filings
            import re
            # Find potential section titles
            section_pattern = re.compile(r"ITEM\s+\d+[A-Z]?\.\s+.*", re.IGNORECASE)
            matches = list(section_pattern.finditer(raw_text))

            if matches:
                last_end = 0
                for i, match in enumerate(matches):
                    start, end = match.span()
                    if start > last_end:
                        # Add the text before the current match as a segment
                        segments.append({
                            "section_type": "unknown", 
                            "text": raw_text[last_end:start].strip(),
                            "start_page": 0,  # Default values since we don't have page info
                            "end_page": 0
                        })
                    # Add the matched section title and subsequent text as a segment
                    next_start = matches[i+1].span()[0] if i+1 < len(matches) else len(raw_text)
                    segments.append({
                        "section_type": match.group(0).strip(), 
                        "text": raw_text[start:next_start].strip(),
                        "start_page": 0,  # Default values
                        "end_page": 0
                    })
                    last_end = next_start
                # Add any remaining text after the last section
                if last_end < len(raw_text):
                    segments.append({
                        "section_type": "unknown", 
                        "text": raw_text[last_end:].strip(),
                        "start_page": 0,
                        "end_page": 0
                    })
            else:
                # Fallback to simpler segmentation if no patterns found
                approx_segment_size = len(raw_text) // 3 # Just an example
                segments.append({
                    "section_type": "part_1_business", 
                    "text": raw_text[:approx_segment_size],
                    "start_page": 0,
                    "end_page": 0
                })
                segments.append({
                    "section_type": "part_2_financials", 
                    "text": raw_text[approx_segment_size:approx_segment_size*2],
                    "start_page": 0,
                    "end_page": 0
                })
                segments.append({
                    "section_type": "part_3_legal", 
                    "text": raw_text[approx_segment_size*2:],
                    "start_page": 0,
                    "end_page": 0
                })
                logging.warning(f"Simplified segmentation applied for {doc_type} due to no pattern matches.")
        else:
            # Default to a single segment for other document types
            segments.append({
                "section_type": "full_document", 
                "text": raw_text,
                "start_page": 0,
                "end_page": 0
            })
            logging.warning(f"Default single-segment segmentation applied for {doc_type}.")

        # Clean up empty segments
        segments = [s for s in segments if s["text"].strip()]

        logging.info(f"Segmented document into {len(segments)} sections.")
        return segments

    def extract_metadata_from_text(self, raw_text: str, doc_type: str) -> dict:
        """Extracts basic metadata from the raw text."""
        logging.info(f"Extracting metadata from text for document type: {doc_type}...")
        metadata = {}

        import re

        # Try to find a company name
        company_match = re.search(r"COMPANY\s+NAME:\s*(.*)", raw_text, re.IGNORECASE)
        if company_match:
            metadata["company"] = company_match.group(1).strip()
        else:
            # Fallback to previous basic regex if specific pattern not found
            company_match = re.search(r"([A-Z][a-z]+(?: [A-Z][a-z]+)*) Corp", raw_text)
            if company_match:
                metadata["company"] = company_match.group(1)
            else:
                metadata["company"] = "Unknown Company"

        # Try to find a filing date
        date_match = re.search(r"FILING\s+DATE:\s*(\d{1,2}/\d{1,2}/\d{2,4})", raw_text, re.IGNORECASE)
        if date_match:
            metadata["filing_date"] = date_match.group(1)
        else:
            # Fallback to previous basic regex
            date_match = re.search(r"\b(\d{1,2}/\d{1,2}/\d{2,4})\b", raw_text)
            if date_match:
                metadata["filing_date"] = date_match.group(1)
            else:
                metadata["filing_date"] = datetime.datetime.now().strftime("%m/%d/%Y")

        # Set document type
        metadata["doc_type"] = doc_type

        logging.info(f"Extracted metadata: {metadata}")

        return metadata

    def process_document(self, source_url: str, doc_type: str) -> dict:
        """Processes a single document: acquire, parse, clean, segment, and store."""
        logging.info(f"Processing document from {source_url} of type {doc_type}")
        try:
            # 1. Acquire Document
            file_path, doc_format = self.acquire_document(source_url, doc_type)
            if not file_path or not doc_format:
                logging.error("Failed to acquire document.")
                return None

            # 2. Parse Document
            raw_text = self.parse_document(file_path, doc_format)
            if not raw_text:
                logging.error("Failed to parse document.")
                return None

            # 3. Clean Text
            cleaned_text = self.clean_text(raw_text)

            # 4. Segment Document
            segments_data = self.segment_document(cleaned_text, doc_type)
            if not segments_data:
                logging.warning("No segments were created for the document.")
                segments_data = [] # Ensure it's a list

            # 5. Extract Metadata
            metadata = self.extract_metadata_from_text(cleaned_text, doc_type)
            metadata.update({
                'source_url': source_url,
                'doc_type': doc_type,
                'file_path': file_path,
                'ingestion_date': datetime.datetime.now().isoformat(),
                'status': 'processed'
            })

            # 6. Store Document Metadata in MongoDB
            document_id = storage.save_document(metadata)
            logging.info(f"Document metadata saved with ID: {document_id}")

            # 7. Store Segments in MongoDB, linking to the document_id
            if segments_data:
                for seg in segments_data:
                    seg['document_id'] = document_id 
                storage.save_segments(segments_data, document_id)

            return {"document_id": document_id, "metadata": metadata, "num_segments": len(segments_data)}
        except Exception as e:
            logging.error(f"Error processing document {source_url}: {e}", exc_info=True)
            return None

    def run(self, document_list=None):
        """Runs the ingestion pipeline. Can process a list of documents or run in a triggered mode."""
        logging.info("Running Ingestion Pipeline...")

        if document_list is None:
            logging.warning("No document list provided. Running in demonstration mode with a single example document.")
            document_list = [{"url": "http://example.com/financial_report.html", "doc_type": "10-K"}]

        results = []
        for doc_info in document_list:
            source_url = doc_info.get("url")
            doc_type = doc_info.get("doc_type")

            if not source_url or not doc_type:
                logging.error("Skipping document due to missing URL or document type.")
                continue

            result = self.process_document(source_url, doc_type)
            results.append(result)
            
            file_path = doc_info.get("file_path")
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logging.info(f"Cleaned up temporary file: {file_path}")
                except OSError as e:
                    logging.error(f"Error cleaning up temporary file {file_path}: {e}")
                    
        return results

if __name__ == "__main__":
    pipeline = IngestionPipeline()
    pipeline.run()