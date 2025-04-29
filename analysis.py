import pandas as pd
import numpy as np
from collections import defaultdict

def calculate_metric_scores(df, weights=None):
    """
    Calculate a score for each metric based on multiple factors.
    
    Args:
        df: DataFrame with preprocessed metric data
        weights: Dictionary of weights for each factor
        
    Returns:
        Dictionary with metric index as key and score as value
    """
    # Default weights if none provided
    if weights is None:
        weights = {
            "Visible_in_Dashboard": 0.1,
            "Used_in_Decision_Making": 0.3,
            "Executive_Requested": 0.1,
            "Review_Score": 0.2,
            "Usage_Score": 0.2,
            "Notes_Score": 0.1
        }
    
    # Normalize weights to sum to 1
    total_weight = sum(weights.values())
    normalized_weights = {k: v/total_weight for k, v in weights.items()}
    
    scores = {}
    
    for idx, row in df.iterrows():
        # Calculate weighted score
        score = (
            normalized_weights["Visible_in_Dashboard"] * (1 if row["Visible_in_Dashboard"] else 0) +
            normalized_weights["Used_in_Decision_Making"] * (1 if row["Used_in_Decision_Making"] else 0) +
            normalized_weights["Executive_Requested"] * (1 if row["Executive_Requested"] else 0) +
            normalized_weights["Review_Score"] * (row["Review_Score"] / 4) +  # Normalize to 0-1
            normalized_weights["Usage_Score"] * (row["Usage_Score"] / 4) +  # Normalize to 0-1
            normalized_weights["Notes_Score"] * (row["Notes_Score"] / 4)  # Normalize to 0-1
        )
        
        scores[idx] = score
    
    return scores

def classify_metrics(df):
    """
    Classify metrics into High Impact, Vanity, Remove, or Improve categories.
    
    Args:
        df: DataFrame with preprocessed metric data
        
    Returns:
        Dictionary with metric index as key and classification as value
    """
    classifications = {}
    
    for idx, row in df.iterrows():
        # High Impact: Used in decision making and either visible in dashboard or executive requested
        if row["Used_in_Decision_Making"] and (row["Visible_in_Dashboard"] or row["Executive_Requested"]):
            classifications[idx] = "High Impact"
        
        # Vanity: Visible but not used for decisions and has vanity/optics in notes
        elif row["Visible_in_Dashboard"] and not row["Used_in_Decision_Making"] and \
             ("vanity" in row["Interpretation_Notes"].lower() or "optics" in row["Interpretation_Notes"].lower()):
            classifications[idx] = "Vanity"
        
        # Remove: Not visible, not used for decisions, low review/usage scores
        elif not row["Visible_in_Dashboard"] and not row["Used_in_Decision_Making"] and \
             row["Review_Score"] <= 2 and row["Usage_Score"] <= 2:
            classifications[idx] = "Remove"
        
        # Improve: Everything else
        else:
            classifications[idx] = "Improve"
    
    return classifications

def get_recommendations(df):
    """
    Generate recommendations for metrics to keep, remove, improve, and potential duplicates.
    
    Args:
        df: DataFrame with processed metrics data and classifications
        
    Returns:
        Tuple of (keep_indices, remove_indices, improve_indices, duplicate_metrics)
    """
    # Metrics to keep (high impact)
    keep_indices = df[df["Classification"] == "High Impact"].index.tolist()
    
    # Metrics to remove (classified as Remove or Vanity with low scores)
    remove_indices = df[(df["Classification"] == "Remove") | 
                        ((df["Classification"] == "Vanity") & (df["Score"] < 0.3))].index.tolist()
    
    # Metrics to improve
    improve_indices = df[(df["Classification"] == "Improve") | 
                         ((df["Classification"] == "Vanity") & (df["Score"] >= 0.3))].index.tolist()
    
    # Find potential duplicate metrics across departments
    metric_departments = defaultdict(list)
    for idx, row in df.iterrows():
        metric_departments[row["Metric_Name"]].append(row["Department"])
    
    # Filter for metrics that appear in multiple departments
    duplicate_metrics = {metric: depts for metric, depts in metric_departments.items() if len(depts) > 1}
    
    return keep_indices, remove_indices, improve_indices, duplicate_metrics
