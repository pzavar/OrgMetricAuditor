import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from io import StringIO

from utils import preprocess_data, load_sample_data
from analysis import (
    calculate_metric_scores, 
    classify_metrics, 
    get_top_metrics,
    get_vanity_metrics,
    find_duplicate_metrics
)
from visualization import (
    create_key_metrics_breakdown,
    create_metrics_by_department, 
    create_metric_value_factors,
    create_top_metrics_table,
    get_color_for_classification
)

# Set page config
st.set_page_config(
    page_title="KPI Audit Tool",
    page_icon="📊",
    layout="wide"
)

# Page title and description
st.title("KPI Audit Tool")
st.markdown("""
This tool analyzes your organization's metrics to identify high-value KPIs 
and recommend eliminating vanity metrics that don't drive decision-making.
""")

# Sidebar
st.sidebar.title("KPI Audit Controls")

# Data upload
st.sidebar.header("1. Data Input")
upload_option = st.sidebar.radio(
    "Choose data source:",
    ["Use sample data", "Upload CSV file"]
)

# Initialize df variable
df = None

if upload_option == "Upload CSV file":
    uploaded_file = st.sidebar.file_uploader("Upload metrics CSV file", type=["csv"])
    if uploaded_file is not None:
        try:
            # Read and process the uploaded file
            content = uploaded_file.getvalue().decode('utf-8')
            df = pd.read_csv(StringIO(content))
            df = preprocess_data(df)
        except Exception as e:
            st.sidebar.error(f"Error loading file: {e}")
            # Fall back to sample data
            df = load_sample_data()
    else:
        # No file uploaded, show instructions
        st.sidebar.info("Please upload a CSV file with metrics data or use the sample data.")
        # Default to sample data if no file is uploaded
        df = load_sample_data()
else:
    # Use sample data
    df = load_sample_data()

# Display data availability status
if df is not None:
    st.sidebar.success(f"Data loaded: {len(df)} metrics available")
    
    # Data filtering options
    st.sidebar.header("2. Filter Data")
    
    # Department filter
    departments = ["All Departments"] + sorted(df["Department"].unique().tolist())
    selected_department = st.sidebar.selectbox("Filter by Department", departments)
    
    # Metric type filter
    metric_types = ["All Metrics"] + sorted(df["Metric_Name"].unique().tolist())
    selected_metric = st.sidebar.selectbox("Filter by Metric Type", metric_types)
    
    # Filter data based on selection
    filtered_df = df.copy()
    if selected_department != "All Departments":
        filtered_df = filtered_df[filtered_df["Department"] == selected_department]
    if selected_metric != "All Metrics":
        filtered_df = filtered_df[filtered_df["Metric_Name"] == selected_metric]
    
    # Search functionality
    st.sidebar.header("3. Search")
    search_term = st.sidebar.text_input("Search metrics by name or notes")
    if search_term:
        search_term = search_term.lower()
        search_mask = (
            filtered_df["Metric_Name"].str.lower().str.contains(search_term) | 
            filtered_df["Interpretation_Notes"].str.lower().str.contains(search_term)
        )
        filtered_df = filtered_df[search_mask]
    
    # Define default weights
    default_weights = {
        "Used_in_Decision_Making": 0.5,
        "Visible_in_Dashboard": 0.1,
        "Executive_Requested": 0.1,
        "Review_Score": 0.15,
        "Usage_Score": 0.15
    }
    
    # Use session state for weights to persist between interactions
    if 'weights' not in st.session_state:
        st.session_state.weights = default_weights.copy()
    
    # Add settings expander (hidden by default)
    st.sidebar.header("4. Advanced Settings")
    with st.sidebar.expander("Analysis Settings", expanded=False):
        # Create a form for the settings
        with st.form(key="analysis_settings"):
            st.write("#### Metric Evaluation Weights")
            st.write("Adjust how much each factor contributes to the metric value score.")
            
            # Create sliders for weights
            temp_weights = {}
            temp_weights["Used_in_Decision_Making"] = st.slider(
                "Weight for Decision Making Usage", 
                0.0, 1.0, st.session_state.weights["Used_in_Decision_Making"], 0.1,
                help="How important is it that a metric is used in actual decision making?"
            )
            
            temp_weights["Visible_in_Dashboard"] = st.slider(
                "Weight for Dashboard Visibility", 
                0.0, 1.0, st.session_state.weights["Visible_in_Dashboard"], 0.1,
                help="How important is it that a metric appears in dashboards?"
            )
            
            temp_weights["Executive_Requested"] = st.slider(
                "Weight for Executive Request", 
                0.0, 1.0, st.session_state.weights["Executive_Requested"], 0.1,
                help="How important is executive sponsorship for a metric?"
            )
            
            temp_weights["Review_Score"] = st.slider(
                "Weight for Review Frequency", 
                0.0, 1.0, st.session_state.weights["Review_Score"], 0.05,
                help="How much does regular review matter?"
            )
            
            temp_weights["Usage_Score"] = st.slider(
                "Weight for Decision Usage", 
                0.0, 1.0, st.session_state.weights["Usage_Score"], 0.05,
                help="How much does recency of use in decision-making matter?"
            )
            
            st.write("##### Classification Thresholds")
            threshold = st.slider(
                "High Impact Threshold", 
                3, 6, 5, 1,
                help="How strict should the classification be? Higher values mean fewer metrics will be considered high-impact."
            )
            
            # Submit button for the form
            submit_button = st.form_submit_button(label="Apply & Save Settings")
            
            if submit_button:
                st.session_state.weights = temp_weights.copy()
                st.session_state.threshold = threshold
                st.success("Settings updated! Analysis will reflect your changes.")
    
    # Get weights from session state
    score_weights = st.session_state.weights
    
    # Store threshold in session state if not already there
    if 'threshold' not in st.session_state:
        st.session_state.threshold = 5  # Default threshold
    
    # Run analysis with current weights
    metric_scores = calculate_metric_scores(filtered_df, weights=score_weights)
    # Pass threshold to classify_metrics
    classified_metrics = classify_metrics(filtered_df, threshold=st.session_state.threshold)
    
    # Check if metric_scores is empty (which can happen with empty filtered data)
    if not metric_scores:
        st.warning("No metrics match your filter criteria. Try adjusting your filters.")
        st.stop()
    
    # Create DataFrame from metric_scores dictionary
    metric_scores_df = pd.DataFrame({"Score": metric_scores})
    
    # Combine the dataframes
    analysis_df = pd.merge(
        filtered_df, 
        metric_scores_df.reset_index().rename(columns={"index": "Metric_ID"}), 
        left_index=True, right_on="Metric_ID"
    )
    
    # Add classification
    analysis_df["Classification"] = pd.Series(classified_metrics)
    
    # Main content area - simplified to 2 tabs
    tab1, tab2 = st.tabs(["Analysis", "Metrics Details"])
    
    with tab1:
        st.header("KPI Value Analysis")
        
        # Key metrics overview
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Count total metrics
            total_metrics = len(analysis_df)
            high_impact = sum(analysis_df["Classification"] == "High Impact")
            vanity = sum(analysis_df["Classification"] == "Vanity")
            
            # Create metrics summary
            st.subheader("Metrics Summary")
            summary_cols = st.columns(2)
            summary_cols[0].metric("High Impact Metrics", high_impact, f"{high_impact/total_metrics:.0%}")
            summary_cols[1].metric("Vanity Metrics", vanity, f"{vanity/total_metrics:.0%}")
            
            # Show key metrics breakdown visualization
            fig = create_key_metrics_breakdown(analysis_df)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Show metrics by department  
            dept_fig = create_metrics_by_department(analysis_df)
            st.plotly_chart(dept_fig, use_container_width=True)
        
        # Top metrics to keep
        st.subheader("Top High-Impact Metrics")
        st.markdown("These metrics have the highest value scores and should be central to decision making:")
        
        # Get top metrics
        top_metrics_df = get_top_metrics(analysis_df, classified_metrics, metric_scores)
        
        if len(top_metrics_df) > 0:
            # Display as table with HTML styling
            st.markdown(create_top_metrics_table(top_metrics_df), unsafe_allow_html=True)
            
            if len(top_metrics_df) < 3:
                st.info("Only a few metrics were classified as high-impact. This suggests most of your metrics aren't directly tied to decision-making.")
        else:
            st.warning("No high-impact metrics found. Consider revising how metrics are used for decision making.")
        
        # Top vanity metrics to consider eliminating
        st.subheader("Top Vanity Metrics to Consider Eliminating")
        st.markdown("These metrics provide minimal value and should be considered for removal from dashboards:")
        
        # Get bottom metrics
        vanity_metrics_df = get_vanity_metrics(analysis_df, classified_metrics, metric_scores, limit=5)
        
        if len(vanity_metrics_df) > 0:
            # Create a simple table view
            vanity_table = vanity_metrics_df[["Department", "Metric_Name", "Score", "Interpretation_Notes"]].copy()
            vanity_table.columns = ["Department", "Metric", "Value Score", "Notes"]
            vanity_table["Value Score"] = vanity_table["Value Score"].map("{:.0%}".format)
            
            st.dataframe(vanity_table, use_container_width=True)
        else:
            st.info("No vanity metrics found with current filters.")
        
        # Find potential duplicate metrics
        duplicate_metrics = find_duplicate_metrics(filtered_df)
        
        if duplicate_metrics:
            st.subheader("Potential Duplicate Metrics")
            st.markdown("These metrics appear across multiple departments and could be consolidated:")
            
            # Create a more visual representation of duplicates
            for metric, depts in duplicate_metrics.items():
                if len(depts) > 1:  # Only show true duplicates
                    st.markdown(f"**{metric}** appears in: {', '.join(depts)}")
    
    with tab2:
        st.header("Metrics Details")
        
        # Option to view all metrics or detailed view of single metric
        view_option = st.radio(
            "Select view:",
            ["View all metrics", "Analyze individual metric"]
        )
        
        if view_option == "View all metrics":
            # Show complete metrics table with value assessment
            st.subheader("Complete Metrics Assessment")
            
            # Create a styled table
            table_df = analysis_df[["Department", "Metric_Name", "Visible_in_Dashboard", 
                                   "Used_in_Decision_Making", "Last_Reviewed",
                                   "Metric_Last_Used_For_Decision", "Score", 
                                   "Classification", "Interpretation_Notes"]].copy()
            
            # Sort by score and add color coding
            table_df = table_df.sort_values(by="Score", ascending=False)
            
            # Define color function for classification
            def color_classification(val):
                if val == "High Impact":
                    return 'background-color: rgba(46, 204, 113, 0.3)'
                else:  # Vanity
                    return 'background-color: rgba(231, 76, 60, 0.3)'
            
            # Show styled dataframe
            st.dataframe(table_df.style.map(color_classification, subset=['Classification']), 
                       use_container_width=True)
            
            # Option to download results
            st.subheader("Export Results")
            
            col1, col2 = st.columns([1, 3])
            export_format = col1.selectbox("Export format:", ["CSV", "Excel"])
            
            if col2.button("Export Analysis"):
                # Prepare export dataframe
                export_df = analysis_df[["Department", "Metric_Name", "Visible_in_Dashboard", 
                                       "Used_in_Decision_Making", "Executive_Requested", 
                                       "Last_Reviewed", "Metric_Last_Used_For_Decision",
                                       "Score", "Classification", "Interpretation_Notes"]]
                
                if export_format == "CSV":
                    csv = export_df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name="kpi_audit_results.csv",
                        mime="text/csv",
                    )
                else:  # Excel
                    # For Excel, we use a workaround with BytesIO since Streamlit doesn't directly support Excel
                    import io
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                        export_df.to_excel(writer, sheet_name='KPI Audit', index=False)
                        # Get the workbook and add some formatting
                        workbook = writer.book
                        worksheet = writer.sheets['KPI Audit']
                        format_header = workbook.add_format({'bold': True, 'bg_color': '#D9E1F2', 'border': 1})
                        for col_num, value in enumerate(export_df.columns.values):
                            worksheet.write(0, col_num, value, format_header)
                        worksheet.set_column(0, len(export_df.columns)-1, 15)
                    
                    st.download_button(
                        label="Download Excel",
                        data=buffer.getvalue(),
                        file_name="kpi_audit_results.xlsx",
                        mime="application/vnd.ms-excel",
                    )
            
        else:  # Analyze individual metric
            # Interactive metric selection and analysis
            st.subheader("Individual Metric Analysis")
            
            # Metric selection
            selected_metric_row = st.selectbox("Select a metric to analyze:", 
                                             options=analysis_df.index, 
                                             format_func=lambda x: f"{analysis_df.loc[x, 'Department']} - {analysis_df.loc[x, 'Metric_Name']}")
            
            if selected_metric_row is not None:
                metric_data = analysis_df.loc[selected_metric_row]
                
                # Display metric details
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    # Basic information
                    st.markdown(f"**Department:** {metric_data['Department']}")
                    st.markdown(f"**Metric Name:** {metric_data['Metric_Name']}")
                    st.markdown(f"**Classification:** {metric_data['Classification']}")
                    st.markdown(f"**Value Score:** {metric_data['Score']:.0%}")
                    
                    # Additional details
                    st.markdown("#### Metric Details")
                    st.markdown(f"**Last Reviewed:** {metric_data['Last_Reviewed']}")
                    st.markdown(f"**Last Used for Decision:** {metric_data['Metric_Last_Used_For_Decision']}")
                    st.markdown(f"**Notes:** {metric_data['Interpretation_Notes']}")
                
                with col2:
                    # Show value factors chart
                    factor_fig = create_metric_value_factors(metric_data)
                    st.plotly_chart(factor_fig, use_container_width=True)
                
                # Value assessment
                st.subheader("Value Assessment")
                
                if metric_data["Classification"] == "High Impact":
                    st.success("""
                    This is a high-impact metric that provides significant value:
                    - Continue using this metric in dashboards and decision-making
                    - Ensure it's regularly reviewed and updated
                    - Consider elevating its visibility across the organization
                    """)
                else:
                    st.warning("""
                    This appears to be a vanity metric with limited decision-making value:
                    - Consider removing from main dashboards to reduce clutter
                    - If keeping, clearly document how it should drive decisions
                    - Review whether resources spent tracking this metric could be better allocated
                    """)
else:
    st.error("No data available. Please upload a CSV file or select the sample data option.")