import pandas as pd
import numpy as np
from collections import defaultdict

def calculate_metric_scores(df, weights=None):
    """
    Calculate a score for each metric based on multiple factors with stricter criteria.
    
    Args:
        df: DataFrame with preprocessed metric data
        weights: Dictionary of weights for each factor
        
    Returns:
        Dictionary with metric index as key and score as value
    """
    # Default weights if none provided - heavily weight decision making
    if weights is None:
        weights = {
            "Used_in_Decision_Making": 0.5,  # Heavily weight actual decision usage
            "Visible_in_Dashboard": 0.1,
            "Executive_Requested": 0.1,
            "Review_Score": 0.15,
            "Usage_Score": 0.15
        }
    
    # Normalize weights to sum to 1
    total_weight = sum(weights.values())
    normalized_weights = {k: v/total_weight for k, v in weights.items()}
    
    scores = {}
    
    for idx, row in df.iterrows():
        # Notes quality factor - penalize vanity metrics and those used for optics
        notes_factor = 0.5 if ("vanity" in row["Interpretation_Notes"].lower() or 
                              "optics" in row["Interpretation_Notes"].lower()) else 1.0
        
        # Real goals bonus
        real_goals_bonus = 0.2 if "tied to real goals" in row["Interpretation_Notes"].lower() else 0.0
        
        # Calculate weighted score with stricter criteria
        score = (
            normalized_weights["Used_in_Decision_Making"] * (1 if row["Used_in_Decision_Making"] else 0) +
            normalized_weights["Visible_in_Dashboard"] * (1 if row["Visible_in_Dashboard"] else 0) +
            normalized_weights["Executive_Requested"] * (1 if row["Executive_Requested"] else 0) +
            normalized_weights["Review_Score"] * (row["Review_Score"] / 4) +
            normalized_weights["Usage_Score"] * (row["Usage_Score"] / 4)
        )
        
        # Apply notes factor and real goals bonus
        score = score * notes_factor + real_goals_bonus
        
        # Cap at 1.0
        score = min(score, 1.0)
        
        scores[idx] = score
    
    return scores

def classify_metrics(df):
    """
    Classify metrics into High Impact or Vanity with stricter criteria.
    Only 3-6 metrics should be classified as truly high impact.
    
    Args:
        df: DataFrame with preprocessed metric data
        
    Returns:
        Dictionary with metric index as key and classification as value
    """
    classifications = {}
    
    for idx, row in df.iterrows():
        # Calculate a strict "value score" independent of the overall score
        value_score = 0
        
        # Used in decision making is critical
        if row["Used_in_Decision_Making"]:
            value_score += 3
            
        # Recent usage indicates value
        if row["Metric_Last_Used_For_Decision"] in ["Recently", "2 weeks ago"]:
            value_score += 2
        elif row["Metric_Last_Used_For_Decision"] in ["Used in QBR", "Last quarter"]:
            value_score += 1
            
        # Recent review indicates relevance
        if row["Last_Reviewed"] in ["This week", "Last month"]:
            value_score += 1
            
        # Tied to real goals is important
        if "tied to real goals" in row["Interpretation_Notes"].lower():
            value_score += 2
            
        # Executive requested might add some value
        if row["Executive_Requested"]:
            value_score += 1
            
        # Negative factors
        if "vanity" in row["Interpretation_Notes"].lower():
            value_score -= 2
            
        if "optics" in row["Interpretation_Notes"].lower():
            value_score -= 2
            
        if "unclear" in row["Interpretation_Notes"].lower():
            value_score -= 1
        
        # Classify based on strict value score
        if value_score >= 5:  # Very strict threshold for high impact
            classifications[idx] = "High Impact"
        else:
            classifications[idx] = "Vanity"  # Simplify to just two categories
    
    return classifications

def get_top_metrics(df, classification_dict, score_dict, limit=5):
    """
    Get the top metrics based on score and classification.
    
    Args:
        df: DataFrame with metric data
        classification_dict: Dictionary with index to classification mapping
        score_dict: Dictionary with index to score mapping
        limit: Maximum number of metrics to return
        
    Returns:
        DataFrame with top metrics
    """
    # Create a combined DataFrame with scores and classifications
    result_df = df.copy()
    result_df["Score"] = pd.Series(score_dict)
    result_df["Classification"] = pd.Series(classification_dict)
    
    # Get only the high impact metrics
    high_impact_df = result_df[result_df["Classification"] == "High Impact"]
    
    # Sort by score in descending order and take top N
    if len(high_impact_df) > limit:
        return high_impact_df.sort_values("Score", ascending=False).head(limit)
    
    return high_impact_df.sort_values("Score", ascending=False)

def get_vanity_metrics(df, classification_dict, score_dict, limit=10):
    """
    Get the vanity metrics to potentially eliminate.
    
    Args:
        df: DataFrame with metric data
        classification_dict: Dictionary with index to classification mapping
        score_dict: Dictionary with index to score mapping
        limit: Maximum number of metrics to return
        
    Returns:
        DataFrame with vanity metrics
    """
    # Create a combined DataFrame with scores and classifications
    result_df = df.copy()
    result_df["Score"] = pd.Series(score_dict)
    result_df["Classification"] = pd.Series(classification_dict)
    
    # Get only the vanity metrics
    vanity_df = result_df[result_df["Classification"] == "Vanity"]
    
    # Sort by score in ascending order and take bottom N
    return vanity_df.sort_values("Score").head(limit)

def find_duplicate_metrics(df):
    """
    Find metrics that appear across multiple departments.
    
    Args:
        df: DataFrame with metric data
        
    Returns:
        Dictionary mapping metric names to lists of departments
    """
    # Group metrics by name and collect departments
    metric_departments = defaultdict(list)
    for idx, row in df.iterrows():
        metric_departments[row["Metric_Name"]].append(row["Department"])
    
    # Filter for metrics that appear in multiple departments
    duplicate_metrics = {metric: depts for metric, depts in metric_departments.items() if len(depts) > 1}
    
    return duplicate_metrics