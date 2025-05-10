import os
import logging
from pathlib import Path

def load_document(file_path):
    """
    Load document content based on environment variable setting.
    If USE_EXAMPLE_TEXT is True, loads example text instead of processing the PDF.
    If file_path contains #file:example_financial_text.txt, directly use the example file
    
    Args:
        file_path (str): Path to the document file
        
    Returns:
        str: Document text content
    """
    use_example = os.environ.get("USE_EXAMPLE_TEXT", "false").lower() == "true"
    
    # Check if special file path identifier is used
    if file_path == "#file:example_financial_text.txt" or use_example:
        try:
            example_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                       "example_financial_text.txt")
            with open(example_path, "r", encoding="utf-8") as f:
                content = f.read()
            logging.info("Using example financial text instead of processing PDF.")
            return content
        except Exception as e:
            logging.error(f"Error reading example text: {e}")
            return "Example financial text could not be loaded."
    else:
        return process_pdf(file_path)

def process_pdf(file_path):
    """
    Process PDF file and extract text content.
    
    Args:
        file_path (str): Path to the PDF file
        
    Returns:
        str: Extracted text from PDF
    """
    try:
        # Import here to avoid issues if PyMuPDF is not installed
        import fitz
        
        logging.info(f"Processing PDF file: {file_path}")
        doc = fitz.open(file_path)
        text = ""
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += page.get_text()
            
        return text
    except ImportError:
        logging.error("PyMuPDF (fitz) is not installed. Cannot process PDF.")
        return "PDF processing failed: PyMuPDF not installed."
    except Exception as e:
        logging.error(f"Error processing PDF: {e}")
        return f"PDF processing failed: {str(e)}"
