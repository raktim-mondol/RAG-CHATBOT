import sys
import os
import logging
import json
from datetime import datetime

# Add project root to path to allow imports from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.config import LOGGING_CONFIG

# Configure logging
logging.basicConfig(level=getattr(logging, LOGGING_CONFIG["level"]), 
                   format=LOGGING_CONFIG["format"])

# Custom JSON encoder to handle datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class PredictionLogger:
    """Logger for model predictions and feedback."""
    
    def __init__(self, log_dir="logs"):
        """Initialize the prediction logger."""
        self.log_dir = log_dir
        
        # Create log directories if they don't exist
        self.predictions_dir = os.path.join(log_dir, "predictions")
        self.corrections_dir = os.path.join(log_dir, "corrections")
        self.feedback_dir = os.path.join(log_dir, "feedback")
        
        os.makedirs(self.predictions_dir, exist_ok=True)
        os.makedirs(self.corrections_dir, exist_ok=True)
        os.makedirs(self.feedback_dir, exist_ok=True)
        
        logging.info(f"PredictionLogger initialized with log directory: {log_dir}")

    def log_prediction(self, document_id, prediction):
        """
        Log a prediction for a document.
        
        Args:
            document_id: ID of the document being analyzed
            prediction: The prediction object to log
        """
        try:
            # Create a filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{document_id}_{timestamp}.json"
            filepath = os.path.join(self.predictions_dir, filename)
            
            # Add timestamp to prediction if not present
            if "timestamp" not in prediction:
                prediction["timestamp"] = datetime.now().isoformat()
                
            # Add document_id to prediction if not present
            if "document_id" not in prediction:
                prediction["document_id"] = document_id
                
            # Write prediction to file
            with open(filepath, 'w') as f:
                json.dump(prediction, f, indent=4, cls=DateTimeEncoder)
                
            logging.info(f"Prediction for document {document_id} logged to {filepath}")
            return True
        except Exception as e:
            logging.error(f"Error logging prediction for document {document_id}: {e}")
            return False

    def log_correction(self, document_id, correction):
        """
        Log a correction for a prediction.
        
        Args:
            document_id: ID of the document being corrected
            correction: The correction data to log
        """
        try:
            # Create a filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{document_id}_{timestamp}.json"
            filepath = os.path.join(self.corrections_dir, filename)
            
            # Add timestamp to correction if not present
            if "timestamp" not in correction:
                correction["timestamp"] = datetime.now().isoformat()
                
            # Add document_id to correction if not present
            if "document_id" not in correction:
                correction["document_id"] = document_id
                
            # Write correction to file
            with open(filepath, 'w') as f:
                json.dump(correction, f, indent=4, cls=DateTimeEncoder)
                
            logging.info(f"Correction for document {document_id} logged to {filepath}")
            return True
        except Exception as e:
            logging.error(f"Error logging correction for document {document_id}: {e}")
            return False

    def log_feedback(self, document_id, feedback):
        """
        Log user feedback.
        
        Args:
            document_id: ID of the document being given feedback
            feedback: The feedback data to log
        """
        try:
            # Create a filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{document_id}_{timestamp}.json"
            filepath = os.path.join(self.feedback_dir, filename)
            
            # Add timestamp to feedback if not present
            if "timestamp" not in feedback:
                feedback["timestamp"] = datetime.now().isoformat()
                
            # Add document_id to feedback if not present
            if "document_id" not in feedback:
                feedback["document_id"] = document_id
                
            # Write feedback to file
            with open(filepath, 'w') as f:
                json.dump(feedback, f, indent=4, cls=DateTimeEncoder)
                
            logging.info(f"Feedback for document {document_id} logged to {filepath}")
            return True
        except Exception as e:
            logging.error(f"Error logging feedback for document {document_id}: {e}")
            return False

    def get_prediction(self, document_id):
        """
        Retrieve the most recent prediction for a document.
        
        Args:
            document_id: ID of the document
            
        Returns:
            dict: The prediction data or None if not found
        """
        try:
            # Find all prediction files for this document
            prediction_files = [f for f in os.listdir(self.predictions_dir) 
                               if f.startswith(f"{document_id}_") and f.endswith(".json")]
            
            if not prediction_files:
                logging.warning(f"No prediction found for document {document_id}")
                return None
                
            # Sort by timestamp (which is part of the filename)
            prediction_files.sort(reverse=True)
            
            # Load the most recent prediction
            with open(os.path.join(self.predictions_dir, prediction_files[0]), 'r') as f:
                prediction = json.load(f)
                
            return prediction
        except Exception as e:
            logging.error(f"Error retrieving prediction for document {document_id}: {e}")
            return None

    def get_corrections(self, document_id):
        """
        Retrieve all corrections for a document.
        
        Args:
            document_id: ID of the document
            
        Returns:
            list: List of correction data or empty list if none found
        """
        try:
            # Find all correction files for this document
            correction_files = [f for f in os.listdir(self.corrections_dir) 
                              if f.startswith(f"{document_id}_") and f.endswith(".json")]
            
            if not correction_files:
                logging.warning(f"No corrections found for document {document_id}")
                return []
                
            # Sort by timestamp (which is part of the filename)
            correction_files.sort(reverse=True)
            
            # Load all corrections
            corrections = []
            for file in correction_files:
                with open(os.path.join(self.corrections_dir, file), 'r') as f:
                    correction = json.load(f)
                    corrections.append(correction)
                    
            return corrections
        except Exception as e:
            logging.error(f"Error retrieving corrections for document {document_id}: {e}")
            return []

    def get_all_predictions(self):
        """
        Retrieve all predictions.
        
        Returns:
            list: List of all prediction data
        """
        try:
            # Find all prediction files
            prediction_files = [f for f in os.listdir(self.predictions_dir) if f.endswith(".json")]
            
            # Load all predictions
            predictions = []
            for file in prediction_files:
                with open(os.path.join(self.predictions_dir, file), 'r') as f:
                    prediction = json.load(f)
                    predictions.append(prediction)
                    
            return predictions
        except Exception as e:
            logging.error(f"Error retrieving all predictions: {e}")
            return []

    def get_all_corrections(self):
        """
        Retrieve all corrections.
        
        Returns:
            list: List of all correction data
        """
        try:
            # Find all correction files
            correction_files = [f for f in os.listdir(self.corrections_dir) if f.endswith(".json")]
            
            # Load all corrections
            corrections = []
            for file in correction_files:
                with open(os.path.join(self.corrections_dir, file), 'r') as f:
                    correction = json.load(f)
                    corrections.append(correction)
                    
            return corrections
        except Exception as e:
            logging.error(f"Error retrieving all corrections: {e}")
            return []

# Create a singleton instance for global use
prediction_logger = PredictionLogger()

# Export convenience functions that use the singleton
def log_prediction(document_id, prediction):
    return prediction_logger.log_prediction(document_id, prediction)

def log_correction(document_id, correction):
    return prediction_logger.log_correction(document_id, correction)

def log_feedback(document_id, feedback):
    return prediction_logger.log_feedback(document_id, feedback)

def get_prediction(document_id):
    return prediction_logger.get_prediction(document_id)

def get_corrections(document_id):
    return prediction_logger.get_corrections(document_id)

def get_all_predictions():
    return prediction_logger.get_all_predictions()

def get_all_corrections():
    return prediction_logger.get_all_corrections()

if __name__ == "__main__":
    # Example usage
    dummy_prediction = {
        "extracted_metrics": {
            "Total Revenue": "$1.2 billion",
            "Net Income": "$300 million"
        },
        "sentiment": "Positive",
        "risks": "Market volatility, currency fluctuations",
        "summary": "Strong financial performance with growth in all segments."
    }
    
    log_prediction("example_doc_123", dummy_prediction)
    
    dummy_correction = {
        "corrections": {
            "metrics": {
                "Total Revenue": "$1.3 billion"
            },
            "sentiment": "Neutral"
        }
    }
    
    log_correction("example_doc_123", dummy_correction)
    
    print("Predictions and corrections logged successfully.")