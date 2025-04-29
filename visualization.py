import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

def create_metric_health_dashboard(df):
    """
    Create a comprehensive health dashboard for all metrics.
    
    Args:
        df: DataFrame with processed metrics data
    
    Returns:
        Plotly figure object
    """
    # Create a scatter plot with different dimensions
    fig = px.scatter(
        df,
        x="Score",
        y="Review_Score",
        size="Usage_Score",
        color="Classification",
        hover_name="Metric_Name",
        hover_data=["Department", "Interpretation_Notes"],
        text="Metric_Name",
        color_discrete_map={
            "High Impact": "#2ecc71",
            "Vanity": "#f1c40f",
            "Remove": "#e74c3c",
            "Improve": "#3498db"
        },
        size_max=15,
        opacity=0.7,
        title="Metric Health Dashboard"
    )
    
    # Customize the appearance
    fig.update_layout(
        xaxis_title="Overall Metric Score",
        yaxis_title="Review Frequency",
        legend_title="Classification",
        height=600,
        plot_bgcolor='rgba(240, 240, 240, 0.5)',
        paper_bgcolor='white',
        font=dict(size=12)
    )
    
    # Add shaped regions to indicate score ranges
    fig.add_shape(
        type="rect",
        x0=0.7, y0=0,
        x1=1, y1=4,
        line=dict(color="green", width=1),
        fillcolor="rgba(46, 204, 113, 0.1)",
        layer="below"
    )
    
    fig.add_shape(
        type="rect",
        x0=0, y0=0,
        x1=0.3, y1=4,
        line=dict(color="red", width=1),
        fillcolor="rgba(231, 76, 60, 0.1)",
        layer="below"
    )
    
    # Add annotations for the regions
    fig.add_annotation(
        x=0.85, y=3.8,
        text="High Performing",
        showarrow=False,
        font=dict(color="green", size=12)
    )
    
    fig.add_annotation(
        x=0.15, y=3.8,
        text="Poor Performing",
        showarrow=False,
        font=dict(color="red", size=12)
    )
    
    # Hide text that would overlap
    fig.update_traces(textposition='top center', textfont_size=10)
    
    return fig

def create_department_metrics_chart(df):
    """
    Create a bar chart showing metrics by department and classification.
    
    Args:
        df: DataFrame with processed metrics data
    
    Returns:
        Plotly figure object
    """
    # Count metrics by department and classification
    dept_class_counts = df.groupby(["Department", "Classification"]).size().reset_index(name="Count")
    
    # Create a grouped bar chart
    fig = px.bar(
        dept_class_counts,
        x="Department",
        y="Count",
        color="Classification",
        color_discrete_map={
            "High Impact": "#2ecc71",
            "Vanity": "#f1c40f",
            "Remove": "#e74c3c",
            "Improve": "#3498db"
        },
        title="Metrics by Department and Classification",
        barmode="group"
    )
    
    # Customize the appearance
    fig.update_layout(
        xaxis_title="Department",
        yaxis_title="Number of Metrics",
        legend_title="Classification",
        plot_bgcolor='rgba(240, 240, 240, 0.5)',
        paper_bgcolor='white',
        font=dict(size=12)
    )
    
    return fig

def create_metrics_classification_chart(df):
    """
    Create a bar chart showing metrics classification distribution.
    
    Args:
        df: DataFrame with processed metrics data
    
    Returns:
        Plotly figure object
    """
    # Count metrics by classification
    class_counts = df["Classification"].value_counts().reset_index()
    class_counts.columns = ["Classification", "Count"]
    
    # Sort by count descending
    class_counts = class_counts.sort_values("Count", ascending=False)
    
    # Create a bar chart
    fig = px.bar(
        class_counts,
        x="Classification",
        y="Count",
        color="Classification",
        color_discrete_map={
            "High Impact": "#2ecc71",
            "Vanity": "#f1c40f",
            "Remove": "#e74c3c",
            "Improve": "#3498db"
        },
        title="Metrics Classification Distribution"
    )
    
    # Add percentage labels
    total = class_counts["Count"].sum()
    for i, row in class_counts.iterrows():
        fig.add_annotation(
            x=row["Classification"],
            y=row["Count"],
            text=f"{row['Count']} ({row['Count']/total:.1%})",
            showarrow=False,
            yshift=10,
            font=dict(size=12)
        )
    
    # Customize the appearance
    fig.update_layout(
        xaxis_title="Classification",
        yaxis_title="Number of Metrics",
        plot_bgcolor='rgba(240, 240, 240, 0.5)',
        paper_bgcolor='white',
        font=dict(size=12)
    )
    
    return fig

def create_metric_scores_radar_chart(metric_data):
    """
    Create a radar chart for an individual metric's scores.
    
    Args:
        metric_data: Series with processed metric data for a single row
    
    Returns:
        Plotly figure object
    """
    # Define the categories for the radar chart
    categories = [
        'Dashboard Visibility', 
        'Decision Making Usage',
        'Executive Requested', 
        'Review Frequency',
        'Usage Recency',
        'Quality of Notes'
    ]
    
    # Extract the values for each category (normalized to 0-1)
    values = [
        1 if metric_data["Visible_in_Dashboard"] else 0,
        1 if metric_data["Used_in_Decision_Making"] else 0,
        1 if metric_data["Executive_Requested"] else 0,
        metric_data["Review_Score"] / 4,  # Normalize to 0-1
        metric_data["Usage_Score"] / 4,  # Normalize to 0-1
        metric_data["Notes_Score"] / 4  # Normalize to 0-1
    ]
    
    # Close the loop for the radar chart
    categories = categories + [categories[0]]
    values = values + [values[0]]
    
    # Create the radar chart
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name=f'{metric_data["Department"]} - {metric_data["Metric_Name"]}',
        line_color=get_color_for_classification(metric_data["Classification"]),
        fillcolor=get_color_for_classification(metric_data["Classification"], alpha=0.2)
    ))
    
    # Add a reference "perfect" metric
    fig.add_trace(go.Scatterpolar(
        r=[1, 1, 1, 1, 1, 1, 1],
        theta=categories,
        fill='none',
        name='Ideal Metric',
        line=dict(color='gray', dash='dash')
    ))
    
    # Customize the appearance
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )
        ),
        title=f"Metric Analysis: {metric_data['Metric_Name']}",
        showlegend=True
    )
    
    return fig

def get_color_for_classification(classification, alpha=1.0):
    """Get color for a classification category."""
    colors = {
        "High Impact": f"rgba(46, 204, 113, {alpha})",
        "Vanity": f"rgba(241, 196, 15, {alpha})",
        "Remove": f"rgba(231, 76, 60, {alpha})",
        "Improve": f"rgba(52, 152, 219, {alpha})"
    }
    return colors.get(classification, f"rgba(149, 165, 166, {alpha})")
