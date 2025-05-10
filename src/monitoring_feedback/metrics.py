import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from scipy import stats
import sys
import os
import logging

# Add project root to path to allow imports from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.config import LOGGING_CONFIG

# Configure logging
logging.basicConfig(level=getattr(logging, LOGGING_CONFIG["level"]), 
                   format=LOGGING_CONFIG["format"])

def calculate_precision_recall(gold_data: list, predictions: list):
    """
    Calculate precision and recall metrics for extraction tasks.
    
    Args:
        gold_data: List of ground truth values/labels
        predictions: List of predicted values/labels corresponding to gold_data
    
    Returns:
        dict: Dictionary containing precision, recall, and f1-score
    """
    logging.info("Calculating precision and recall...")
    
    if not gold_data or not predictions:
        logging.warning("Empty gold data or predictions provided")
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
        
    if len(gold_data) != len(predictions):
        logging.warning(f"Length mismatch: gold_data ({len(gold_data)}) vs predictions ({len(predictions)})")
        # Trim to the shorter length
        min_len = min(len(gold_data), len(predictions))
        gold_data = gold_data[:min_len]
        predictions = predictions[:min_len]
    
    try:
        # For binary classification
        if all(isinstance(x, (bool, int)) and x in (0, 1, True, False) for x in gold_data + predictions):
            precision = precision_score(gold_data, predictions)
            recall = recall_score(gold_data, predictions)
            f1 = f1_score(gold_data, predictions)
            return {"precision": float(precision), "recall": float(recall), "f1": float(f1)}
        
        # For exact match (string or other values)
        true_positives = sum(1 for g, p in zip(gold_data, predictions) if g == p and g is not None)
        
        if all(g is None for g in gold_data):
            # Edge case: all gold data is None
            precision = 0.0
        else:
            precision = true_positives / sum(1 for p in predictions if p is not None)
            
        recall = true_positives / sum(1 for g in gold_data if g is not None)
        
        # Calculate F1 score
        if precision + recall == 0:
            f1 = 0.0
        else:
            f1 = 2 * (precision * recall) / (precision + recall)
            
        return {"precision": float(precision), "recall": float(recall), "f1": float(f1)}
        
    except Exception as e:
        logging.error(f"Error calculating precision/recall: {e}")
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0, "error": str(e)}

def detect_drift(current_data_distribution: dict, baseline_distribution: dict):
    """
    Detect data drift between current and baseline distributions using KS-test.
    
    Args:
        current_data_distribution: Dictionary with feature names as keys and lists of values as values
        baseline_distribution: Dictionary with feature names as keys and lists of values as values
    
    Returns:
        dict: Dictionary with drift detection results for each feature
    """
    logging.info("Detecting data drift...")
    
    if not current_data_distribution or not baseline_distribution:
        logging.warning("Empty distribution provided")
        return {"drift_detected": False, "error": "Empty distribution provided"}
    
    results = {"drift_detected": False, "features": {}}
    
    try:
        for feature in current_data_distribution:
            if feature not in baseline_distribution:
                logging.warning(f"Feature '{feature}' not found in baseline distribution")
                continue
                
            current_values = current_data_distribution[feature]
            baseline_values = baseline_distribution[feature]
            
            # Convert values to numpy arrays
            current_np = np.array(current_values, dtype=float)
            baseline_np = np.array(baseline_values, dtype=float)
            
            # Handle NaN values
            current_np = current_np[~np.isnan(current_np)]
            baseline_np = baseline_np[~np.isnan(baseline_np)]
            
            if len(current_np) < 2 or len(baseline_np) < 2:
                logging.warning(f"Not enough non-NaN values for feature '{feature}'")
                continue
                
            # Perform KS-test
            statistic, p_value = stats.ks_2samp(current_np, baseline_np)
            
            # Check if drift detected (p-value < 0.05)
            drift_detected = p_value < 0.05
            
            results["features"][feature] = {
                "drift_detected": drift_detected,
                "statistic": float(statistic),
                "p_value": float(p_value)
            }
            
            if drift_detected:
                results["drift_detected"] = True
                
        return results
        
    except Exception as e:
        logging.error(f"Error detecting drift: {e}")
        return {"drift_detected": False, "error": str(e)}

def calculate_accuracy_metrics(gold_standard: list, predictions: list):
    """
    Calculate accuracy metrics for predictions.
    
    Args:
        gold_standard: List of ground truth values
        predictions: List of predicted values
    
    Returns:
        dict: Dictionary containing accuracy, precision, recall, and f1 score
    """
    if not gold_standard or not predictions:
        return {
            "accuracy": 0.0,
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0
        }

    # Calculate basic accuracy
    correct = sum(1 for g, p in zip(gold_standard, predictions) if g == p)
    accuracy = correct / len(gold_standard) if len(gold_standard) > 0 else 0.0

    # Get precision/recall metrics
    pr_metrics = calculate_precision_recall(gold_standard, predictions)

    return {
        "accuracy": float(accuracy),
        "precision": pr_metrics["precision"],
        "recall": pr_metrics["recall"],
        "f1": pr_metrics["f1"]
    }

def calculate_rouge_score(reference_summaries, generated_summaries):
    """
    Calculate ROUGE scores for summary evaluation.
    
    Args:
        reference_summaries: List of reference summaries
        generated_summaries: List of generated summaries to evaluate
        
    Returns:
        dict: Dictionary with ROUGE-1, ROUGE-2, and ROUGE-L scores
    """
    try:
        from rouge import Rouge
        
        if not reference_summaries or not generated_summaries:
            return {"rouge-1": 0.0, "rouge-2": 0.0, "rouge-l": 0.0}
        
        # ROUGE expects non-empty strings
        filtered_refs = [ref for ref in reference_summaries if ref and ref.strip()]
        filtered_gens = [gen for gen in generated_summaries if gen and gen.strip()]
        
        if not filtered_refs or not filtered_gens:
            return {"rouge-1": 0.0, "rouge-2": 0.0, "rouge-l": 0.0}
            
        # Ensure equal length
        min_len = min(len(filtered_refs), len(filtered_gens))
        filtered_refs = filtered_refs[:min_len]
        filtered_gens = filtered_gens[:min_len]
            
        rouge = Rouge()
        scores = rouge.get_scores(filtered_gens, filtered_refs, avg=True)
        
        return {
            "rouge-1": float(scores["rouge-1"]["f"]),
            "rouge-2": float(scores["rouge-2"]["f"]),
            "rouge-l": float(scores["rouge-l"]["f"])
        }
    except ImportError:
        logging.warning("Rouge package not installed. Install with pip install rouge.")
        return {"rouge-1": 0.0, "rouge-2": 0.0, "rouge-l": 0.0, "error": "Rouge package not installed"}
    except Exception as e:
        logging.error(f"Error calculating ROUGE scores: {e}")
        return {"rouge-1": 0.0, "rouge-2": 0.0, "rouge-l": 0.0, "error": str(e)}