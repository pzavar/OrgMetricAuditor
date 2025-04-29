import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from io import StringIO

from utils import preprocess_data, load_sample_data
from analysis import classify_metrics, calculate_metric_scores, get_recommendations
from visualization import (
    create_metric_health_dashboard,
    create_department_metrics_chart,
    create_metrics_classification_chart,
    create_metric_scores_radar_chart
)

# Set page config
st.set_page_config(
    page_title="KPI Audit Tool",
    page_icon="📊",
    layout="wide"
)

# Header
st.title("KPI Audit Tool")
st.markdown("""
This tool analyzes your organization's metrics to identify valuable KPIs 
and recommend eliminating vanity metrics that don't drive decision-making.
""")

# Sidebar
st.sidebar.image("https://images.unsplash.com/photo-1542744173-05336fcc7ad4", use_container_width=True)
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
    
    # Add analyzer options
    st.sidebar.header("4. Analysis Options")
    score_weights = {
        "Visible_in_Dashboard": st.sidebar.slider("Weight for Dashboard Visibility", 0.0, 1.0, 0.1, 0.1),
        "Used_in_Decision_Making": st.sidebar.slider("Weight for Decision Making Usage", 0.0, 1.0, 0.3, 0.1),
        "Executive_Requested": st.sidebar.slider("Weight for Executive Request", 0.0, 1.0, 0.1, 0.1),
        "Review_Score": st.sidebar.slider("Weight for Review Frequency", 0.0, 1.0, 0.2, 0.1),
        "Usage_Score": st.sidebar.slider("Weight for Decision Usage", 0.0, 1.0, 0.2, 0.1),
        "Notes_Score": st.sidebar.slider("Weight for Quality of Notes", 0.0, 1.0, 0.1, 0.1)
    }
    
    # Run analysis
    classified_metrics = classify_metrics(filtered_df)
    metric_scores = calculate_metric_scores(filtered_df, weights=score_weights)
    
    # Check if metric_scores is empty (which can happen with empty filtered data)
    if not metric_scores:
        st.warning("No metrics match your filter criteria. Try adjusting your filters.")
        st.stop()
    
    # Create DataFrame from metric_scores dictionary (handle empty case)
    metric_scores_df = pd.DataFrame({"Score": metric_scores})
    
    # Combine the dataframes
    analysis_df = pd.merge(
        filtered_df, 
        metric_scores_df.reset_index().rename(columns={"index": "Metric_ID"}), 
        left_index=True, right_on="Metric_ID"
    )
    
    # Add classification
    analysis_df["Classification"] = classified_metrics
    
    # Main content area
    tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Metric Analysis", "Department Insights", "Recommendations"])
    
    with tab1:
        st.header("Metrics Health Dashboard")

        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        # Count metrics by classification
        classification_counts = analysis_df["Classification"].value_counts().to_dict()
        high_impact = classification_counts.get("High Impact", 0)
        vanity = classification_counts.get("Vanity", 0)
        remove = classification_counts.get("Remove", 0)
        improve = classification_counts.get("Improve", 0)
        
        col1.metric("High Impact Metrics", high_impact, f"{high_impact/len(analysis_df):.0%}")
        col2.metric("Vanity Metrics", vanity, f"{vanity/len(analysis_df):.0%}")
        col3.metric("Candidates for Removal", remove, f"{remove/len(analysis_df):.0%}")
        col4.metric("Metrics to Improve", improve, f"{improve/len(analysis_df):.0%}")
        
        # Visualization of metric health
        st.subheader("Metric Health Overview")
        fig = create_metric_health_dashboard(analysis_df)
        st.plotly_chart(fig, use_container_width=True)
        
        # Department distribution
        st.subheader("Metrics by Department")
        dept_fig = create_department_metrics_chart(analysis_df)
        st.plotly_chart(dept_fig, use_container_width=True)
        
    with tab2:
        st.header("Metric Analysis")
        
        # Metrics classification
        st.subheader("Metrics Classification")
        class_fig = create_metrics_classification_chart(analysis_df)
        st.plotly_chart(class_fig, use_container_width=True)
        
        # Table view of metrics with scores
        st.subheader("Metrics Scores")
        # Format the table
        table_df = analysis_df[["Department", "Metric_Name", "Visible_in_Dashboard", 
                               "Used_in_Decision_Making", "Executive_Requested", 
                               "Score", "Classification", "Interpretation_Notes"]].copy()
        
        # Sort by score and add color
        table_df = table_df.sort_values(by="Score", ascending=False)
        
        # Add color coding based on classification
        def color_classification(val):
            if val == "High Impact":
                return 'background-color: rgba(46, 204, 113, 0.3)'
            elif val == "Vanity":
                return 'background-color: rgba(241, 196, 15, 0.3)'
            elif val == "Remove":
                return 'background-color: rgba(231, 76, 60, 0.3)'
            else:  # Improve
                return 'background-color: rgba(52, 152, 219, 0.3)'
                
        # Show styled dataframe
        st.dataframe(table_df.style.map(color_classification, subset=['Classification']), 
                    use_container_width=True)
        
        # Detailed metric view
        st.subheader("Individual Metric Analysis")
        selected_metric_row = st.selectbox("Select a metric to analyze:", 
                                         options=analysis_df.index, 
                                         format_func=lambda x: f"{analysis_df.loc[x, 'Department']} - {analysis_df.loc[x, 'Metric_Name']}")
        
        if selected_metric_row is not None:
            metric_data = analysis_df.loc[selected_metric_row]
            
            # Display metric details
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Department:** {metric_data['Department']}")
                st.write(f"**Metric Name:** {metric_data['Metric_Name']}")
                st.write(f"**Classification:** {metric_data['Classification']}")
                st.write(f"**Overall Score:** {metric_data['Score']:.2f}")
                st.write(f"**Interpretation Notes:** {metric_data['Interpretation_Notes']}")
            
            with col2:
                # Radar chart for the metric
                radar_fig = create_metric_scores_radar_chart(metric_data)
                st.plotly_chart(radar_fig, use_container_width=True)
    
    with tab3:
        st.header("Department Insights")
        
        # Department selection for detailed view
        dept_options = sorted(df["Department"].unique().tolist())
        selected_dept = st.selectbox("Select Department for Analysis:", dept_options)
        
        # Filter data for selected department
        dept_df = df[df["Department"] == selected_dept].copy()
        dept_classified = classify_metrics(dept_df)
        dept_scores = calculate_metric_scores(dept_df, weights=score_weights)
        
        # Create DataFrame from dept_scores dictionary
        if not dept_scores:
            # Handle empty data case
            st.warning(f"No metrics data available for {selected_dept}.")
            st.stop()
            
        dept_scores_df = pd.DataFrame({"Score": dept_scores})
        
        # Combine data
        dept_analysis_df = pd.merge(
            dept_df, 
            dept_scores_df.reset_index().rename(columns={"index": "Metric_ID"}), 
            left_index=True, right_on="Metric_ID"
        )
        dept_analysis_df["Classification"] = dept_classified
        
        # Department metrics overview
        st.subheader(f"Metrics Overview for {selected_dept}")
        
        col1, col2, col3 = st.columns(3)
        dept_metrics_count = len(dept_analysis_df)
        dept_high_impact = sum(dept_analysis_df["Classification"] == "High Impact")
        dept_vanity = sum(dept_analysis_df["Classification"] == "Vanity")
        dept_remove = sum(dept_analysis_df["Classification"] == "Remove")
        
        col1.metric("Total Metrics", dept_metrics_count)
        col2.metric("High Impact", dept_high_impact, f"{dept_high_impact/dept_metrics_count:.0%}")
        col3.metric("Metrics to Remove/Improve", dept_vanity + dept_remove, 
                  f"{(dept_vanity + dept_remove)/dept_metrics_count:.0%}")
        
        # Chart for department metrics
        st.subheader(f"Metrics Breakdown for {selected_dept}")
        
        # Create pie chart for department metrics classification
        dept_class_counts = dept_analysis_df["Classification"].value_counts().reset_index()
        dept_class_counts.columns = ["Classification", "Count"]
        
        dept_pie = px.pie(
            dept_class_counts, 
            values="Count", 
            names="Classification",
            color="Classification",
            color_discrete_map={
                "High Impact": "#2ecc71",
                "Vanity": "#f1c40f",
                "Remove": "#e74c3c",
                "Improve": "#3498db"
            },
            title=f"Metrics Classification for {selected_dept}"
        )
        st.plotly_chart(dept_pie, use_container_width=True)
        
        # Department metrics table
        st.subheader(f"All Metrics for {selected_dept}")
        dept_table = dept_analysis_df[["Metric_Name", "Visible_in_Dashboard", 
                                     "Used_in_Decision_Making", "Executive_Requested", 
                                     "Score", "Classification", "Interpretation_Notes"]].copy()
        dept_table = dept_table.sort_values(by="Score", ascending=False)
        
        st.dataframe(dept_table.style.map(color_classification, subset=['Classification']), 
                   use_container_width=True)
        
    with tab4:
        st.header("KPI Recommendations")
        
        # Get recommendations
        keep, remove, improve, duplicate = get_recommendations(analysis_df)
        
        # Display recommendations
        st.subheader("Metrics to Keep")
        st.info(f"These {len(keep)} metrics are high-impact and should remain central to your dashboards and decision-making.")
        
        if len(keep) > 0:
            keep_df = analysis_df.loc[keep][["Department", "Metric_Name", "Score", "Interpretation_Notes"]]
            st.dataframe(keep_df.sort_values(by="Score", ascending=False), use_container_width=True)
        
        st.subheader("Metrics to Remove")
        st.error(f"Consider removing these {len(remove)} metrics that provide little value and clutter your dashboards.")
        
        if len(remove) > 0:
            remove_df = analysis_df.loc[remove][["Department", "Metric_Name", "Score", "Interpretation_Notes"]]
            st.dataframe(remove_df.sort_values(by="Score", ascending=True), use_container_width=True)
        
        st.subheader("Metrics to Improve")
        st.warning(f"These {len(improve)} metrics have potential but need refinement to become more actionable.")
        
        if len(improve) > 0:
            improve_df = analysis_df.loc[improve][["Department", "Metric_Name", "Score", "Interpretation_Notes"]]
            improve_df = improve_df.sort_values(by="Score", ascending=False)
            
            # Add improvement suggestions based on notes
            improve_df["Improvement Suggestion"] = improve_df["Interpretation_Notes"].apply(
                lambda x: "Link to decision-making processes" if "vanity" in x.lower() 
                else "Clarify ownership and review regularly" if "unclear" in x.lower() 
                else "Document relevance to business outcomes" if "optics" in x.lower()
                else "Establish regular review and decision-making usage"
            )
            
            st.dataframe(improve_df, use_container_width=True)
        
        # Potential duplicate metrics
        if len(duplicate) > 0:
            st.subheader("Potential Duplicate Metrics")
            st.warning(f"You have {len(duplicate)} metrics that appear across multiple departments. Consider consolidating these:")
            
            for metric, depts in duplicate.items():
                st.markdown(f"**{metric}** appears in: {', '.join(depts)}")
        
        # Export options
        st.subheader("Export Analysis")
        export_type = st.radio("Export format:", ["CSV", "Excel"])
        
        if st.button("Export Analysis"):
            # Prepare export dataframe
            export_df = analysis_df[["Department", "Metric_Name", "Visible_in_Dashboard", 
                                   "Used_in_Decision_Making", "Executive_Requested", 
                                   "Last_Reviewed", "Metric_Last_Used_For_Decision",
                                   "Score", "Classification", "Interpretation_Notes"]]
            
            if export_type == "CSV":
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
        
        # Next steps guidance
        st.subheader("Next Steps")
        st.markdown("""
        Once you've reviewed these recommendations, consider:
        
        1. **Implement a Metric Governance Process** - Establish a regular review cadence for all metrics
        2. **Link Metrics to Business Outcomes** - Ensure every metric directly ties to a business objective
        3. **Reduce Dashboard Clutter** - Remove the identified vanity metrics from main dashboards
        4. **Consolidate Duplicate Metrics** - Standardize metrics that appear across multiple departments
        5. **Create Tiered Dashboards** - Primary dashboard with high-impact metrics, secondary dashboards for details
        """)

else:
    st.error("No data available. Please upload a CSV file or select the sample data option.")
