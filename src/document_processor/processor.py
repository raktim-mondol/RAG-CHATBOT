import os
import logging
from pathlib import Path

class DocumentProcessor:
    def __init__(self):
        """Initialize the document processor."""
        self.logger = logging.getLogger(__name__)

    def load_document(self, file_path):
        """Load document content based on file type and settings."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        # Handle text files
        if file_path.lower().endswith('.txt'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.logger.info(f"Successfully loaded text file: {file_path}")
                return content
            except Exception as e:
                self.logger.error(f"Error reading text file: {e}")
                raise
        
        # Handle PDFs
        elif file_path.lower().endswith('.pdf'):
            return self._process_pdf(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_path}")

    def _process_pdf(self, file_path):
        """Process PDF file and extract text content."""
        try:
            import fitz
            self.logger.info(f"Processing PDF file: {file_path}")
            doc = fitz.open(file_path)
            text = ""
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text += page.get_text()
            return text
        except ImportError:
            self.logger.error("PyMuPDF (fitz) is not installed. Cannot process PDF.")
            return "PDF processing failed: PyMuPDF not installed."
        except Exception as e:
            self.logger.error(f"Error processing PDF: {e}")
            return f"PDF processing failed: {str(e)}"

    def clean_text(self, text):
        """Clean and normalize text content by removing extra whitespace."""
        if not text:
            return ""
        # Split on whitespace and rejoin with single spaces
        return ' '.join(word for word in text.split() if word)

    def segment_document(self, content):
        """Segment document into logical sections."""
        if not content or not isinstance(content, str):
            return []
            
        segments = []
        current_section = "default"
        current_text = []
        
        lines = content.split("\n")
        
        for line in lines:
            line = line.strip()
            if line.startswith(("#", "Section", "SECTION")):
                # Save previous section if it exists
                if current_text:
                    segments.append({
                        "section_type": current_section,
                        "text": "\n".join(filter(None, current_text)),
                        "start_page": 1,
                        "end_page": 1
                    })
                current_section = line.lstrip("#").strip()
                current_text = []
            elif line:  # Only add non-empty lines
                current_text.append(line)
                
        # Add the last section or default section if no sections were found
        if current_text:
            segments.append({
                "section_type": current_section,
                "text": "\n".join(filter(None, current_text)),
                "start_page": 1,
                "end_page": 1
            })
            
        return segments

    def extract_tables(self, content):
        """Extract tables from the document."""
        if not content:
            return []
            
        tables = []
        current_table = []
        
        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("|"):
                current_table.append(line)
            elif current_table:
                if len(current_table) > 2:  # At least header and separator
                    tables.append(current_table.copy())
                current_table = []
                
        # Add last table if exists
        if current_table and len(current_table) > 2:
            tables.append(current_table)
            
        return tables