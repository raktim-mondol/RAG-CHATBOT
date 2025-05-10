import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import json
from datetime import datetime
import numpy as np
from scipy import stats

# Add project root to path to allow imports from src
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)
from src.monitoring_feedback.metrics import calculate_accuracy_metrics, detect_drift
from src.monitoring_feedback.logger import PredictionLogger

class TestMonitoringFeedback(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.logger = PredictionLogger()
        self.test_doc_id = "test_123"
        self.test_predictions = {
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "Revenue": "$100M",
                "Profit": "$20M"
            },
            "sentiment": "Positive",
            "risks": ["competition", "regulatory"]
        }
        
        self.test_corrections = {
            "corrections": {
                "metrics": {
                    "Revenue": "$110M"  # Corrected value
                }
            },
            "feedback": "Revenue value was incorrect"
        }
        
    def test_log_prediction(self):
        """Test prediction logging"""
        result = self.logger.log_prediction(self.test_doc_id, self.test_predictions)
        self.assertTrue(result)
        
    def test_log_correction(self):
        """Test correction logging"""
        result = self.logger.log_correction(self.test_doc_id, self.test_corrections)
        self.assertTrue(result)
        
    def test_calculate_metrics(self):
        """Test accuracy metrics calculation"""
        predictions = ["$100M", "$20M", "15%"]
        gold_standard = ["$110M", "$20M", "15%"]
        
        metrics = calculate_accuracy_metrics(gold_standard, predictions)
        
        self.assertIn("accuracy", metrics)
        self.assertIn("precision", metrics)
        self.assertIn("recall", metrics)
        self.assertIn("f1", metrics)
        
    def test_drift_detection(self):
        """Test distribution drift detection"""
        current_distribution = {
            "Revenue": [100, 200, 150],
            "Profit": [20, 30, 25]
        }
        baseline_distribution = {
            "Revenue": [90, 180, 140],
            "Profit": [18, 28, 23]
        }
        
        drift_results = detect_drift(current_distribution, baseline_distribution)
        
        self.assertIsInstance(drift_results, dict)
        self.assertIn("drift_detected", drift_results)
        self.assertIn("features", drift_results)
        
if __name__ == '__main__':
    unittest.main()
