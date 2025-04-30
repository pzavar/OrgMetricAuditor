import pandas as pd
import numpy as np
import io

def validate_csv_format(df):
    """
    Validate that a DataFrame has the required columns and format.
    
    Args:
        df: The pandas DataFrame to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    # Required columns
    required_columns = [
        'Department',
        'Metric_Name',
        'Visible_in_Dashboard',
        'Used_in_Decision_Making',
        'Executive_Requested',
        'Last_Reviewed',
        'Metric_Last_Used_For_Decision',
        'Interpretation_Notes'
    ]
    
    # Check for missing columns
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        return False, f"Missing required columns: {', '.join(missing_columns)}"
    
    # Check for Boolean columns format
    bool_columns = ['Visible_in_Dashboard', 'Used_in_Decision_Making', 'Executive_Requested']
    for col in bool_columns:
        invalid_values = df[col][~df[col].isin(['Yes', 'No'])].unique()
        if len(invalid_values) > 0:
            return False, f"Column '{col}' contains invalid values. Only 'Yes' or 'No' are allowed. Found: {list(invalid_values)}"
    
    # Check for Last_Reviewed valid values
    review_values = ['This week', 'Last month', 'Last quarter', 'Unknown']
    invalid_reviews = df['Last_Reviewed'][~df['Last_Reviewed'].isin(review_values)].unique()
    if len(invalid_reviews) > 0:
        return False, f"Column 'Last_Reviewed' contains invalid values. Expected values: {review_values}. Found: {list(invalid_reviews)}"
    
    # Check for Last_Used valid values
    usage_values = ['Recently', '2 weeks ago', 'Last quarter', 'Used in QBR', 'Never', "Don't know"]
    invalid_usage = df['Metric_Last_Used_For_Decision'][~df['Metric_Last_Used_For_Decision'].isin(usage_values)].unique()
    if len(invalid_usage) > 0:
        return False, f"Column 'Metric_Last_Used_For_Decision' contains invalid values. Expected values: {usage_values}. Found: {list(invalid_usage)}"
    
    # All validations passed
    return True, ""

def preprocess_data(df):
    """
    Preprocess the input data for analysis.
    
    Args:
        df: DataFrame to preprocess
        
    Returns:
        processed DataFrame
    
    Raises:
        ValueError: If the DataFrame doesn't have the required format
    """
    # Validate format first
    is_valid, error_message = validate_csv_format(df)
    if not is_valid:
        raise ValueError(error_message)
    
    # Make a copy to avoid modifying the original
    processed_df = df.copy()
    
    # Convert columns to appropriate data types
    bool_columns = ['Visible_in_Dashboard', 'Used_in_Decision_Making', 'Executive_Requested']
    for col in bool_columns:
        processed_df[col] = processed_df[col].map({'Yes': True, 'No': False})
    
    # Convert review frequency to numerical score
    review_map = {
        'This week': 4,
        'Last month': 3,
        'Last quarter': 2,
        'Unknown': 1
    }
    processed_df['Review_Score'] = processed_df['Last_Reviewed'].map(review_map)
    
    # Convert usage frequency to numerical score
    usage_map = {
        'Recently': 4,
        '2 weeks ago': 3,
        'Last quarter': 2,
        'Used in QBR': 2,
        'Never': 1,
        "Don't know": 1
    }
    processed_df['Usage_Score'] = processed_df['Metric_Last_Used_For_Decision'].map(usage_map)
    
    # Score for interpretation notes (whether it's tied to real goals)
    processed_df['Notes_Score'] = processed_df['Interpretation_Notes'].apply(
        lambda x: 4 if 'real goals' in str(x).lower() else
                  3 if 'auto-synced' in str(x).lower() else
                  2 if 'frequently discussed' in str(x).lower() or 'updated manually' in str(x).lower() else
                  1 if 'vanity' in str(x).lower() or 'optics' in str(x).lower() else 2
    )
    
    return processed_df

def get_sample_csv_content():
    """Return the sample CSV content as a string."""
    return """Department,Metric_Name,Visible_in_Dashboard,Used_in_Decision_Making,Executive_Requested,Last_Reviewed,Metric_Last_Used_For_Decision,Interpretation_Notes
Marketing,OKR Progress,No,No,No,This week,2 weeks ago,Drives vanity OKRs
Finance,Leads Generated,Yes,No,No,Last month,Used in QBR,Tied to real goals
Engineering,OKR Progress,Yes,Yes,Yes,Last month,Recently,Auto-synced from tool
Engineering,Daily Active Users,Yes,No,No,Last quarter,Last quarter,Auto-synced from tool
Finance,Code Commits,Yes,No,No,Unknown,Recently,Updated manually
Operations,Email Open Rate,Yes,No,Yes,Unknown,Don't know,Updated manually
Operations,Net Revenue Retention,Yes,No,No,Last quarter,Don't know,Tied to real goals
Marketing,Demo Requests,No,Yes,No,Last month,2 weeks ago,Tied to real goals
Engineering,Revenue,Yes,Yes,No,Last quarter,Last quarter,Used for optics only
Finance,Customer Churn,No,No,No,This week,Used in QBR,Drives vanity OKRs
Sales,Ticket Resolution Time,Yes,No,No,Unknown,Last quarter,Auto-synced from tool
Finance,Ticket Resolution Time,Yes,No,No,Last quarter,Last quarter,Frequently discussed
Sales,Slack Messages Sent,Yes,Yes,No,Last quarter,Don't know,Tied to real goals
Support,New Signups,Yes,No,No,Last quarter,2 weeks ago,Updated manually
Engineering,Customer Escalations,No,No,No,Last month,2 weeks ago,Updated manually
Product,Bug Count,Yes,No,No,Unknown,Last quarter,Tied to real goals
Operations,Ticket Resolution Time,Yes,No,No,Last month,Used in QBR,Unclear ownership
Support,Demo Requests,Yes,Yes,Yes,Last month,2 weeks ago,Tied to real goals
Marketing,Test Coverage,Yes,No,No,This week,2 weeks ago,Drives vanity OKRs
Engineering,Deployment Frequency,No,No,No,Unknown,Never,Tied to real goals
Product,Internal NPS,Yes,Yes,No,This week,Recently,Drives vanity OKRs
Operations,Deployment Frequency,Yes,No,No,Last month,2 weeks ago,Updated manually
Marketing,Internal NPS,Yes,No,No,Unknown,Last quarter,Frequently discussed
Operations,Customer Touchpoints,No,No,No,This week,Last quarter,Auto-synced from tool
Support,Daily Active Users,Yes,No,No,This week,Never,Auto-synced from tool
Engineering,Customer Escalations,Yes,Yes,No,Unknown,2 weeks ago,Auto-synced from tool
Finance,Customer Escalations,Yes,Yes,No,Unknown,Last quarter,Auto-synced from tool
Marketing,Slack Messages Sent,No,Yes,No,Last quarter,Never,Auto-synced from tool
Engineering,Demo Requests,Yes,No,No,Last month,Don't know,Often misinterpreted
Marketing,Daily Active Users,Yes,Yes,No,Last quarter,Don't know,Unclear ownership
Product,Leads Generated,Yes,Yes,No,Unknown,Recently,Drives vanity OKRs
Support,Code Commits,Yes,No,No,Last month,Don't know,Tied to real goals
Operations,Code Commits,Yes,No,No,Last quarter,Used in QBR,Unclear ownership
Marketing,Meetings Booked,Yes,No,No,Last month,Used in QBR,Auto-synced from tool
Finance,Revenue,Yes,No,No,This week,2 weeks ago,Frequently discussed
Finance,App Crashes,No,No,Yes,Unknown,Don't know,Updated manually
Marketing,OKR Progress,Yes,Yes,No,This week,Recently,Often misinterpreted
Product,Bug Count,Yes,Yes,No,This week,Recently,Updated manually
Sales,App Crashes,No,No,No,Unknown,Recently,Used for optics only
Marketing,Customer Escalations,Yes,No,No,This week,Used in QBR,Drives vanity OKRs
Finance,Customer Touchpoints,Yes,No,No,This week,Never,Often misinterpreted
Finance,Customer Escalations,No,No,No,Last month,Recently,Tied to real goals
Product,App Crashes,Yes,Yes,Yes,This week,Used in QBR,Used for optics only
Operations,Email Open Rate,Yes,Yes,Yes,This week,Recently,Often misinterpreted
Engineering,Customer Escalations,Yes,Yes,Yes,Unknown,Last quarter,Frequently discussed
Engineering,Customer Churn,Yes,Yes,No,Last month,Used in QBR,Auto-synced from tool
Engineering,Customer Escalations,Yes,Yes,No,Last month,Recently,Tied to real goals
Product,Slack Messages Sent,Yes,No,No,Unknown,2 weeks ago,Frequently discussed
Product,Net Revenue Retention,No,No,No,Unknown,Last quarter,Used for optics only
Product,OKR Progress,Yes,No,No,Last month,Never,Tied to real goals
Operations,App Crashes,No,Yes,No,Unknown,Recently,Drives vanity OKRs
Sales,Slack Messages Sent,Yes,No,Yes,Unknown,2 weeks ago,Auto-synced from tool
Engineering,Customer Churn,Yes,No,No,This week,Last quarter,Unclear ownership
Operations,Demo Requests,Yes,No,No,Last quarter,2 weeks ago,Updated manually
Sales,Customer Churn,Yes,No,No,Last month,Recently,Tied to real goals
Sales,Ticket Resolution Time,Yes,No,No,Unknown,Never,Auto-synced from tool
Product,Leads Generated,No,No,Yes,Unknown,Last quarter,Auto-synced from tool
Product,Time on Site,No,Yes,No,Last month,Never,Often misinterpreted
Engineering,Demo Requests,No,No,No,Last month,Last quarter,Auto-synced from tool
Finance,Demo Requests,Yes,No,No,Last quarter,Don't know,Frequently discussed"""

def load_sample_data():
    """Load the sample data from the predefined CSV content."""
    # Get the CSV content
    csv_content = get_sample_csv_content()
    
    # Load CSV content into a DataFrame
    df = pd.read_csv(io.StringIO(csv_content))
    
    # Preprocess the data
    return preprocess_data(df)
