import sys
import os
import logging
from datetime import datetime
import json

# Add project root to path to allow imports from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.config import LOGGING_CONFIG
from src.storage_access import storage
from src.monitoring_feedback import logger, metrics

# Configure logging
logging.basicConfig(level=getattr(logging, LOGGING_CONFIG["level"]), 
                   format=LOGGING_CONFIG["format"])

class HumanReviewDashboard:
    """Human-in-the-loop review dashboard for document insights."""
    def __init__(self):
        """Initialize the human review dashboard."""
        logging.info("HumanReviewDashboard initialized.")
        self.current_document_id = None
        self.current_prediction = None
        self.corrections_cache = {}  # Cache for storing corrections before submission
        
    def display_document(self, document_id: str, prediction: dict = None):
        """
        Displays a document and its prediction for review.
        
        Args:
            document_id: The ID of the document to display
            prediction: Optional pre-loaded prediction, if not provided it will be fetched
        """
        # Get document metadata from storage
        document = storage.get_document_by_id(document_id)
        if not document:
            logging.error(f"Document with ID {document_id} not found")
            print(f"Error: Document with ID {document_id} not found")
            return False
            
        # Get document segments
        segments = storage.get_document_segments(document_id)
        
        # Get prediction if not provided
        if prediction is None:
            # Fetch insights related to this document
            insights = storage.get_insights_by_document(document_id)
            if not insights:
                logging.warning(f"No insights found for document {document_id}")
                print(f"No insights found for document {document_id}")
                prediction = {}
            else:
                # Convert insights to prediction format
                # This is a simplification; in a real dashboard, you would use a more structured approach
                prediction = self._convert_insights_to_prediction(insights)
        
        # Set the current document and prediction for later use
        self.current_document_id = document_id
        self.current_prediction = prediction
        self.corrections_cache = {}  # Reset corrections cache
        
        # In a real dashboard, this would render a UI
        # For this implementation, we'll print the information
        print("\n" + "="*50)
        print(f"DOCUMENT REVIEW: {document_id}")
        print("="*50)
        print(f"Company: {document.get('company', 'Unknown')}")
        print(f"Document Type: {document.get('doc_type', 'Unknown')}")
        print(f"Filing Date: {document.get('filing_date', 'Unknown')}")
        print("-"*50)
        print("DOCUMENT SEGMENTS:")
        for i, segment in enumerate(segments):
            print(f"\nSegment {i+1}: {segment.get('section_type', 'Unknown')}")
            # In a real dashboard, you would show just a preview of the text
            text_preview = segment.get('text', '')[:100] + "..." if segment.get('text', '') else "No text"
            print(f"Text Preview: {text_preview}")
        print("-"*50)
        print("EXTRACTED INSIGHTS:")
        if prediction:
            self._display_prediction(prediction)
        else:
            print("No predictions available for this document")
        print("="*50)
        print("To provide corrections, use the correct_insight() method")
        return True
        
    def _display_prediction(self, prediction):
        """Display the prediction in a readable format."""
        # Display extracted metrics
        if "extracted_metrics" in prediction:
            print("\nEXTRACTED METRICS:")
            for metric, value in prediction.get("extracted_metrics", {}).items():
                print(f"  {metric}: {value}")
        
        # Display sentiment analysis
        if "sentiment" in prediction:
            print("\nSENTIMENT ANALYSIS:")
            print(f"  {prediction.get('sentiment', 'Not available')}")
        
        # Display risk identification
        if "risks" in prediction:
            print("\nIDENTIFIED RISKS:")
            print(f"  {prediction.get('risks', 'No risks identified')}")
        
        # Display summary
        if "summary" in prediction:
            print("\nSUMMARY:")
            print(f"  {prediction.get('summary', 'No summary available')}")
    
    def _convert_insights_to_prediction(self, insights):
        """Convert database insights to prediction format."""
        prediction = {
            "extracted_metrics": {},
            "document_id": None,
            "company": None,
            "timestamp": None
        }
        
        for insight in insights:
            # This is a simplification - in a real system, you would have a more structured approach
            id, metric, value, timestamp, company, source_ref, model_version, original_text, page_numbers = insight
            
            # Categorize insights based on metric or other criteria
            if metric.lower() in ["sentiment", "sentiment_analysis"]:
                prediction["sentiment"] = value
            elif metric.lower() in ["risks", "risk_factors"]:
                prediction["risks"] = value
            elif metric.lower() in ["summary", "document_summary"]:
                prediction["summary"] = value
            else:
                # Treat as a regular metric
                prediction["extracted_metrics"][metric] = value
                
            # Set metadata from first insight (assuming all insights have same metadata)
            if prediction["document_id"] is None:
                prediction["document_id"] = source_ref.split("document_id=")[1].split(",")[0] if "document_id=" in source_ref else None
                prediction["company"] = company
                prediction["timestamp"] = timestamp
                prediction["model_version"] = model_version
                
        return prediction
    
    def correct_insight(self, insight_type: str, key: str = None, corrected_value: str = None):
        """
        Collect a correction for an insight. This is a temporary correction that will be stored
        until submit_corrections() is called.
        
        Args:
            insight_type: The type of insight (metrics, sentiment, risks, summary)
            key: For metrics, the specific metric name; for others, can be None
            corrected_value: The corrected value
            
        Returns:
            bool: Whether the correction was accepted
        """
        if not self.current_document_id or not self.current_prediction:
            logging.error("No document currently under review")
            print("Error: No document currently under review. Call display_document() first.")
            return False
            
        # Store the correction in the cache
        if insight_type not in self.corrections_cache:
            self.corrections_cache[insight_type] = {}
            
        if insight_type == "metrics":
            if not key:
                logging.error("Key (metric name) is required for metrics corrections")
                print("Error: Key (metric name) is required for metrics corrections")
                return False
            self.corrections_cache[insight_type][key] = corrected_value
        else:
            self.corrections_cache[insight_type] = corrected_value
            
        print(f"Correction for {insight_type} {key or ''} recorded. Call submit_corrections() to save.")
        return True
        
    def submit_corrections(self):
        """
        Submit all collected corrections for the current document.
        
        Returns:
            dict: The submitted corrections
        """
        if not self.current_document_id or not self.current_prediction:
            logging.error("No document currently under review")
            print("Error: No document currently under review. Call display_document() first.")
            return {}
            
        if not self.corrections_cache:
            logging.warning("No corrections to submit")
            print("Warning: No corrections to submit")
            return {}
            
        # Prepare the correction object
        correction = {
            "document_id": self.current_document_id,
            "timestamp": datetime.now().isoformat(),
            "corrections": self.corrections_cache,
            "original_prediction": self.current_prediction
        }
        
        # Log the correction
        logger.log_correction(self.current_document_id, correction)
        
        # In a real system, you would save the correction to the database
        # and potentially trigger a retraining or fine-tuning process
        print(f"Corrections for document {self.current_document_id} submitted successfully.")
        
        # Clear the cache
        self.corrections_cache = {}
        
        return correction

class AccuracyMetricsDashboard:
    """Dashboard for displaying accuracy metrics and drift alerts."""
    def __init__(self):
        """Initialize the accuracy metrics dashboard."""
        logging.info("AccuracyMetricsDashboard initialized.")
        self.current_metrics = None
        self.baseline_metrics = None
        self.drift_status = False
        
    def load_metrics(self, metrics_data: dict):
        """
        Load metrics data into the dashboard.
        
        Args:
            metrics_data: Dictionary containing metrics data
        """
        self.current_metrics = metrics_data
        print("Metrics data loaded successfully.")
        
    def load_baseline(self, baseline_data: dict):
        """
        Load baseline metrics for comparison.
        
        Args:
            baseline_data: Dictionary containing baseline metrics
        """
        self.baseline_metrics = baseline_data
        print("Baseline data loaded successfully.")
        
    def display_metrics(self, metrics: dict = None):
        """
        Display current metrics or provided metrics.
        
        Args:
            metrics: Optional metrics to display, if not provided will use current_metrics
        """
        metrics_to_display = metrics if metrics else self.current_metrics
        
        if not metrics_to_display:
            print("No metrics data available. Load metrics first using load_metrics().")
            return
            
        print("\n" + "="*50)
        print("ACCURACY METRICS DASHBOARD")
        print("="*50)
        
        # Display precision and recall metrics
        if "precision" in metrics_to_display and "recall" in metrics_to_display:
            print("\nPRECISION-RECALL METRICS:")
            print(f"  Precision: {metrics_to_display.get('precision', 0.0):.4f}")
            print(f"  Recall: {metrics_to_display.get('recall', 0.0):.4f}")
            print(f"  F1 Score: {metrics_to_display.get('f1', 0.0):.4f}")
            
        # Display ROUGE scores if available
        if any(key.startswith("rouge") for key in metrics_to_display):
            print("\nSUMMARIZATION METRICS (ROUGE):")
            for key in ["rouge-1", "rouge-2", "rouge-l"]:
                if key in metrics_to_display:
                    print(f"  {key.upper()}: {metrics_to_display.get(key, 0.0):.4f}")
                    
        # Display other metrics
        print("\nOTHER METRICS:")
        for key, value in metrics_to_display.items():
            if key not in ["precision", "recall", "f1"] and not key.startswith("rouge"):
                if isinstance(value, (int, float)):
                    print(f"  {key}: {value:.4f}")
                else:
                    print(f"  {key}: {value}")
                    
        # Compare with baseline if available
        if self.baseline_metrics:
            print("\nCOMPARISON WITH BASELINE:")
            for key in metrics_to_display:
                if key in self.baseline_metrics and isinstance(metrics_to_display.get(key), (int, float)):
                    baseline_value = self.baseline_metrics.get(key, 0)
                    current_value = metrics_to_display.get(key, 0)
                    difference = current_value - baseline_value
                    print(f"  {key}: {current_value:.4f} ({'+' if difference >= 0 else ''}{difference:.4f} from baseline)")
        
        print("="*50)
        
    def check_drift(self, threshold: float = 0.05):
        """
        Check for metric drift compared to baseline.
        
        Args:
            threshold: The threshold for detecting significant drift
            
        Returns:
            bool: Whether drift was detected
        """
        if not self.current_metrics or not self.baseline_metrics:
            print("Both current metrics and baseline are required for drift detection.")
            return False
            
        significant_drift = False
        drift_details = {}
        
        for key in self.current_metrics:
            if key in self.baseline_metrics and isinstance(self.current_metrics.get(key), (int, float)):
                baseline_value = self.baseline_metrics.get(key, 0)
                current_value = self.current_metrics.get(key, 0)
                
                # Skip values that are exactly zero in both
                if baseline_value == 0 and current_value == 0:
                    continue
                    
                # Calculate relative change if baseline is not zero
                if baseline_value != 0:
                    relative_change = abs((current_value - baseline_value) / baseline_value)
                    is_significant = relative_change > threshold
                else:
                    # If baseline is zero but current is not, that's significant
                    is_significant = current_value != 0
                    relative_change = 1.0  # 100% change
                    
                drift_details[key] = {
                    "baseline": baseline_value,
                    "current": current_value,
                    "relative_change": relative_change,
                    "is_significant": is_significant
                }
                
                if is_significant:
                    significant_drift = True
        
        self.drift_status = significant_drift
        
        return {
            "drift_detected": significant_drift,
            "details": drift_details
        }
        
    def display_drift_alert(self, alert: bool = None):
        """
        Display drift detection alert.
        
        Args:
            alert: Optional override for drift status
        """
        drift_status = self.drift_status if alert is None else alert
        
        print("\n" + "="*50)
        print("DRIFT DETECTION ALERT")
        print("="*50)
        
        if drift_status:
            print("⚠️  ALERT: Significant drift detected in model performance! ⚠️")
            print("It is recommended to investigate the cause and potentially retrain the model.")
        else:
            print("✅ No significant drift detected. Model performance is stable.")
        
        print("="*50)


if __name__ == "__main__":
    # Example usage
    print("\nExample: Human Review Dashboard")
    human_dashboard = HumanReviewDashboard()
    
    # In a real application, these would be real document IDs and predictions
    # For demonstration, we'll use dummy data
    dummy_prediction = {
        "extracted_metrics": {
            "Total Revenue": "$1.2 billion",
            "Net Income": "$300 million",
            "EPS": "$1.45"
        },
        "sentiment": "Positive: The document shows an optimistic outlook on future growth.",
        "risks": "Market volatility, currency fluctuations, increased competition",
        "summary": "The company reported strong Q3 results with revenue growth of 15% YoY."
    }
    
    # In a real system, you would display a real document
    # For demonstration, we'll simulate the display_document method
    print("Simulating document display...")
    # The real method would get document data from the database
    human_dashboard.current_document_id = "doc123"
    human_dashboard.current_prediction = dummy_prediction
    human_dashboard._display_prediction(dummy_prediction)
    
    # Collect corrections
    human_dashboard.correct_insight("metrics", "EPS", "$1.50")
    human_dashboard.correct_insight("sentiment", None, "Neutral: The document presents a balanced view.")
    
    # Submit corrections
    corrections = human_dashboard.submit_corrections()
    print(f"Submitted corrections: {json.dumps(corrections, indent=2)}")
    
    print("\nExample: Accuracy Metrics Dashboard")
    metrics_dashboard = AccuracyMetricsDashboard()
    
    # Load sample metrics and baseline
    current_metrics = {
        "precision": 0.85,
        "recall": 0.78,
        "f1": 0.81,
        "rouge-1": 0.72,
        "rouge-2": 0.45,
        "rouge-l": 0.68
    }
    
    baseline_metrics = {
        "precision": 0.82,
        "recall": 0.80,
        "f1": 0.81,
        "rouge-1": 0.70,
        "rouge-2": 0.43,
        "rouge-l": 0.65
    }
    
    metrics_dashboard.load_metrics(current_metrics)
    metrics_dashboard.load_baseline(baseline_metrics)
    
    # Display metrics
    metrics_dashboard.display_metrics()
    
    # Check for drift
    drift_results = metrics_dashboard.check_drift(threshold=0.05)
    print(f"Drift detection results: {json.dumps(drift_results, indent=2)}")
    
    # Display drift alert
    metrics_dashboard.display_drift_alert()