import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

def create_key_metrics_breakdown(df):
    """
    Create a bar chart showing the distribution of high-impact vs. vanity metrics.
    
    Args:
        df: DataFrame with processed metrics data
    
    Returns:
        Plotly figure object
    """
    # Count metrics by classification
    class_counts = df["Classification"].value_counts().reset_index()
    class_counts.columns = ["Classification", "Count"]
    
    # Create horizontal bar chart with value counts
    fig = px.bar(
        class_counts,
        y="Classification",
        x="Count",
        color="Classification",
        color_discrete_map={
            "High Impact": "#27ae60",  # Green for high impact
            "Vanity": "#e74c3c"       # Red for vanity
        },
        title="Metric Classification Distribution",
        orientation='h',
        text="Count",
        labels={
            "Classification": "Metric Classification", 
            "Count": "Number of Metrics",
            "x": "Number of Metrics"
        },
        category_orders={"Classification": ["High Impact", "Vanity"]}
    )
    
    # Add count labels
    for i, row in class_counts.iterrows():
        fig.add_annotation(
            y=row["Classification"],
            x=row["Count"],
            text=f"{row['Count']} metrics",
            showarrow=False,
            xshift=25,
            font=dict(
                size=16, 
                color="#000000",
                family="Arial"
            ),
            bgcolor="#ffffff",
            borderpad=4
        )
    
    # Customize appearance
    fig.update_layout(
        xaxis_title="Number of Metrics",
        yaxis_title="",
        plot_bgcolor='rgba(240, 240, 240, 0.9)',
        paper_bgcolor='white',
        font=dict(size=14, color="#333333"),
        height=360,
        width=400,
        margin=dict(l=10, r=40, t=40, b=30),
    )
    
    # Ensure y-axis labels are clearly visible
    fig.update_yaxes(
        tickfont=dict(color="#333333", size=14),
        title_font=dict(size=14, color="#333333")
    )
    
    # Ensure x-axis labels are clearly visible
    fig.update_xaxes(
        tickfont=dict(color="#333333", size=14),
        title_font=dict(size=14, color="#333333")
    )
    
    # Make legend more visible and descriptive
    fig.update_layout(
        legend=dict(
            title=dict(
                text="Metric Classification:",
                font=dict(color="black", size=14, family="Arial Bold")
            ),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(240, 240, 240, 0.95)",
            bordercolor="rgba(0, 0, 0, 0.5)",
            borderwidth=1,
            font=dict(size=14, color="black", family="Arial"),
            itemsizing="constant"
        )
    )
    
    # Format the text with better contrast
    fig.update_traces(
        texttemplate='%{text}', 
        textposition='inside',
        textfont=dict(color="white", size=16, family="Arial")
    )
    
    return fig

def create_metrics_by_department(df):
    """
    Create a horizontal bar chart showing metrics by department, split by classification.
    
    Args:
        df: DataFrame with processed metrics data
    
    Returns:
        Plotly figure object
    """
    # Count metrics by department and classification
    dept_counts = df.groupby(["Department", "Classification"]).size().reset_index(name="Count")
    
    # Create a stacked horizontal bar chart
    fig = px.bar(
        dept_counts,
        y="Department",
        x="Count",
        color="Classification",
        color_discrete_map={
            "High Impact": "#27ae60",  # Green for high impact metrics 
            "Vanity": "#e74c3c"       # Red for vanity metrics
        },
        title="Metrics by Department",
        orientation='h',
        text="Count",
        labels={
            "Classification": "Metric Classification", 
            "Count": "Number of Metrics",
            "x": "Number of Metrics"
        },
        category_orders={"Classification": ["High Impact", "Vanity"]}
    )
    
    # Customize appearance
    fig.update_layout(
        xaxis_title="Number of Metrics",
        yaxis_title="",
        plot_bgcolor='rgba(240, 240, 240, 0.9)',
        paper_bgcolor='white',
        font=dict(size=14, color="#333333"),
        height=360,
        width=400,
        bargap=0.2,
        margin=dict(l=10, r=40, t=40, b=30),
        # Make legend more visible and descriptive
        legend=dict(
            title=dict(
                text="Metric Classification:",
                font=dict(color="black", size=14, family="Arial Bold")
            ),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(240, 240, 240, 0.95)",
            bordercolor="rgba(0, 0, 0, 0.5)",
            borderwidth=1,
            font=dict(size=14, color="black", family="Arial"),
            itemsizing="constant"
        ),
    )
    
    # Ensure y-axis labels are clearly visible
    fig.update_yaxes(
        tickfont=dict(color="#333333", size=14),
        title_font=dict(size=14, color="#333333")
    )
    
    # Ensure x-axis labels are clearly visible
    fig.update_xaxes(
        tickfont=dict(color="#333333", size=14),
        title_font=dict(size=14, color="#333333")
    )
    
    # Position text inside bars with better contrast
    fig.update_traces(
        textposition='inside', 
        insidetextanchor='middle',
        textfont=dict(color="white", size=14, family="Arial"),
        insidetextfont=dict(color="white", size=14, family="Arial"),
    )
    
    return fig

def create_metric_value_factors(metric_data):
    """
    Create a bar chart showing the factors contributing to a metric's value.
    
    Args:
        metric_data: Series with processed metric data for a single row
    
    Returns:
        Plotly figure object
    """
    # Define the factors and their values
    factors = [
        'Used for Decision Making',
        'Visible in Dashboard',
        'Executive Requested',
        'Recent Review',
        'Recent Usage',
        'Tied to Real Goals'
    ]
    
    # Calculate values for each factor (0 or 1 for simplicity)
    values = [
        1 if metric_data["Used_in_Decision_Making"] else 0,
        1 if metric_data["Visible_in_Dashboard"] else 0,
        1 if metric_data["Executive_Requested"] else 0,
        1 if metric_data["Last_Reviewed"] in ["This week", "Last month"] else 0,
        1 if metric_data["Metric_Last_Used_For_Decision"] in ["Recently", "2 weeks ago", "Used in QBR"] else 0,
        1 if "tied to real goals" in str(metric_data["Interpretation_Notes"]).lower() else 0
    ]
    
    # Create DataFrame for plotting
    factor_df = pd.DataFrame({"Factor": factors, "Value": values})
    
    # Create bar chart
    fig = px.bar(
        factor_df,
        y="Factor",
        x="Value",
        orientation='h',
        color="Value",
        color_discrete_map={0: "#e74c3c", 1: "#27ae60"},
        title=f"Value Factors: {metric_data['Metric_Name']}",
        text=["No", "No", "No", "No", "No", "No"]
    )
    
    # Update the text to show Yes/No
    for i, value in enumerate(values):
        fig.data[0].text[i] = "Yes" if value == 1 else "No"
    
    # Customize appearance
    fig.update_layout(
        xaxis_title="",
        xaxis=dict(
            tickmode='array',
            tickvals=[0, 1],
            ticktext=['No', 'Yes'],
            range=[-0.1, 1.1]
        ),
        yaxis_title="",
        plot_bgcolor='rgba(240, 240, 240, 0.9)',
        paper_bgcolor='white',
        font=dict(size=14, color="#333333"),
        height=400,
        margin=dict(l=10, r=10, t=40, b=10),
        title_font=dict(size=16, color="#333333")
    )
    
    # Ensure y-axis labels are clearly visible
    fig.update_yaxes(
        tickfont=dict(color="#333333", size=14),
        title_font=dict(size=14, color="#333333")
    )
    
    # Ensure x-axis labels are clearly visible
    fig.update_xaxes(
        tickfont=dict(color="#333333", size=14),
        title_font=dict(size=14, color="#333333")
    )
    
    # Remove legend
    fig.update_layout(showlegend=False)
    
    # Update text position and styling for better contrast
    fig.update_traces(
        textposition='inside', 
        insidetextanchor='middle',
        textfont=dict(color="white", size=16, family="Arial"),
        insidetextfont=dict(color="white", size=16, family="Arial")
    )
    
    return fig

def create_top_metrics_table(df, top_n=5):
    """
    Create a styled HTML table for the top metrics.
    
    Args:
        df: DataFrame with the top metrics
        top_n: Number of top metrics to show
    
    Returns:
        HTML for styled table
    """
    # Limit to top N rows
    df = df.head(top_n)
    
    # Select and rename columns for display
    display_df = df[["Department", "Metric_Name", "Score"]].copy()
    display_df.columns = ["Department", "Metric", "Value Score"]
    
    # Format the score on a 0-10 scale
    display_df["Value Score"] = (display_df["Value Score"] * 10).round(1).map("{:.1f}/10".format)
    
    # Convert to HTML with styling
    html = display_df.to_html(
        index=False,
        classes=["table", "table-striped", "table-hover"],
        border=0
    )
    
    # Add custom CSS
    styled_html = f"""
    <style>
    table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 16px;
    }}
    th {{
        background-color: #2c3e50;
        color: white;
        text-align: left;
        padding: 12px;
    }}
    td {{
        padding: 10px;
        border-bottom: 1px solid #ddd;
    }}
    tr:nth-child(even) {{
        background-color: #f8f9fa;
    }}
    tr:hover {{
        background-color: #e9ecef;
    }}
    </style>
    {html}
    """
    
    return styled_html

def get_color_for_classification(classification, alpha=1.0):
    """Get color for a classification category."""
    colors = {
        "High Impact": f"rgba(39, 174, 96, {alpha})",  # Darker green for better visibility
        "Vanity": f"rgba(231, 76, 60, {alpha})"       # Red
    }
    return colors.get(classification, f"rgba(149, 165, 166, {alpha})")