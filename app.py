import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os
from io import StringIO

from utils import preprocess_data, load_sample_data, validate_csv_format, get_sample_csv_content
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

# Streamlit will use the configuration from .streamlit/config.toml

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
    ["Use sample data", "Upload CSV file"],
    index=0  # Default to sample data
)

# Template download section
if upload_option == "Upload CSV file":
    st.sidebar.markdown("### CSV Template")
    csv_template = get_sample_csv_content()
    
    col1, col2 = st.sidebar.columns(2)
    
    # Download template with full sample data
    col1.download_button(
        label="Download Template",
        data=csv_template,
        file_name="metrics_template.csv",
        mime="text/csv",
        help="Download a CSV template with sample data that matches the required format"
    )
    
    # Download minimal template with just headers and a few rows
    minimal_template = """Department,Metric_Name,Visible_in_Dashboard,Used_in_Decision_Making,Executive_Requested,Last_Reviewed,Metric_Last_Used_For_Decision,Interpretation_Notes
Marketing,Example Metric,Yes,No,No,This week,Recently,Add your notes here
Finance,Another Metric,No,Yes,Yes,Last month,2 weeks ago,Add your notes here"""
    
    col2.download_button(
        label="Empty Template",
        data=minimal_template,
        file_name="empty_template.csv",
        mime="text/csv",
        help="Download an empty CSV template with just the required columns"
    )
    
    # Format requirements explanation
    with st.sidebar.expander("CSV Format Requirements", expanded=False):
        st.markdown("""
        Your CSV file must include these columns:
        
        1. **Department**: Your department name
        2. **Metric_Name**: Name of the metric/KPI
        3. **Visible_in_Dashboard**: Must be 'Yes' or 'No'
        4. **Used_in_Decision_Making**: Must be 'Yes' or 'No'
        5. **Executive_Requested**: Must be 'Yes' or 'No'
        6. **Last_Reviewed**: Must be one of: 'This week', 'Last month', 'Last quarter', 'Unknown'
        7. **Metric_Last_Used_For_Decision**: Must be one of: 'Recently', '2 weeks ago', 'Last quarter', 'Used in QBR', 'Never', 'Don't know'
        8. **Interpretation_Notes**: Free text field for additional context
        """)

# Initialize df variable
df = None

if upload_option == "Upload CSV file":
    uploaded_file = st.sidebar.file_uploader("Upload metrics CSV file", type=["csv"])
    if uploaded_file is not None:
        try:
            # Read and process the uploaded file
            content = uploaded_file.getvalue().decode('utf-8')
            raw_df = pd.read_csv(StringIO(content))
            
            # Check basic format before processing
            is_valid, error_message = validate_csv_format(raw_df)
            
            if is_valid:
                df = preprocess_data(raw_df)
                st.sidebar.success(f"Successfully loaded {len(df)} metrics from your file")
            else:
                st.sidebar.error(f"Invalid CSV format: {error_message}")
                st.sidebar.info("Using sample data instead. Please fix your CSV and re-upload.")
                df = load_sample_data()
                
        except Exception as e:
            st.sidebar.error(f"Error processing file: {str(e)}")
            st.sidebar.info("Using sample data instead. Please check the format requirements and try again.")
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
    
    # Filter data based on department selection
    filtered_df = df.copy()
    if selected_department != "All Departments":
        filtered_df = filtered_df[filtered_df["Department"] == selected_department]
        
        # Show filter status
        st.sidebar.info(f"Filtering by Department: {selected_department}")
        if len(filtered_df) == 0:
            st.sidebar.warning("No metrics match your filter criteria. Try adjusting filters.")
        else:
            st.sidebar.success(f"Showing {len(filtered_df)} of {len(df)} metrics")
    
    # Search functionality was removed as it wasn't working correctly
    
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
    st.sidebar.header("3. Advanced Settings")
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
    
    # Main content area - Using 3 tabs: Analysis, Visualizations, and Metrics Details
    tab1, tab2, tab3 = st.tabs(["Analysis", "Visualizations", "Metrics Details"])
    
    # Calculate the metrics totals and get the required dataframes
    total_metrics = len(analysis_df)
    high_impact = sum(analysis_df["Classification"] == "High Impact")
    vanity = sum(analysis_df["Classification"] == "Vanity")
    high_impact_pct = high_impact/total_metrics
    vanity_pct = vanity/total_metrics
    
    # Get top metrics and vanity metrics
    top_metrics_df = get_top_metrics(analysis_df, classified_metrics, metric_scores)
    vanity_metrics_df = get_vanity_metrics(analysis_df, classified_metrics, metric_scores, limit=5)
    
    # Find potential duplicate metrics
    duplicate_metrics = find_duplicate_metrics(filtered_df)
    
    # Tab 1: Professional Analysis Summary and Detailed Justifications
    with tab1:
        st.header("KPI Audit Analysis")
        
        # Create a metrics summary counter at the top
        col1, col2 = st.columns(2)
        col1.metric("High Impact Metrics", high_impact)
        col2.metric("Vanity Metrics", vanity)
        
        st.markdown("---")
        
        # Executive Summary with McKinsey-style consulting depth
        st.subheader("Executive Summary")
        st.markdown(f"""
        This strategic analysis evaluates your organization's KPI ecosystem using a proprietary multi-factor methodology 
        developed for Fortune 100 companies. Our assessment identifies critical metrics driving business outcomes while 
        surfacing metrics that consume resources without proportionate value creation.
        
        The analysis reveals **{high_impact} high-impact metrics** in your measurement framework, 
        indicating {"significant" if high_impact_pct < 0.3 else "moderate" if high_impact_pct < 0.5 else "limited"} 
        opportunity to optimize your organization's measurement strategy and resource allocation.
        """)
        
        # KPI Portfolio Health - more like a consulting deliverable
        st.markdown("### KPI Portfolio Health Assessment")
        
        # KPI Health metrics
        health_col1, health_col2, health_col3 = st.columns(3)
        
        # Metrics in the first column
        health_col1.metric(
            "Decision-Driving Metrics", 
            f"{high_impact}/{total_metrics}",
            help="Metrics directly influencing business decisions and outcomes"
        )
        
        # Metrics in the second column
        decision_making_count = sum(filtered_df["Used_in_Decision_Making"])
        health_col2.metric(
            "Decision Utilization", 
            f"{decision_making_count}/{total_metrics}",
            help="Percentage of metrics actively leveraged in decision-making processes"
        )
        
        # Metrics in the third column - Duplicate Metrics ratio
        duplicate_count = sum(1 for metric, depts in duplicate_metrics.items() if len(depts) > 1) if duplicate_metrics else 0
        unique_metrics_count = len(set(filtered_df["Metric_Name"]))
        
        health_col3.metric(
            "Metric Redundancy", 
            f"{duplicate_count} metrics",
            help="Degree of metric duplication across departments, indicating siloed measurement"
        )
        
        # Key findings in a formatted box with strategic implications
        st.info(f"""
        ### Strategic Implications
        
        1. **Measurement Efficiency Gap:** {"A critical" if high_impact_pct < 0.3 else "A significant" if high_impact_pct < 0.5 else "A"} 
           proportion of metrics ({vanity} of {total_metrics}) are not driving organizational value, creating opportunity costs 
           through unnecessary reporting and analysis efforts.
        
        2. **Decision Support Effectiveness:** Only {high_impact} of your {total_metrics} metrics directly inform decision-making, 
           {"substantially below" if high_impact_pct < 0.3 else "below" if high_impact_pct < 0.5 else "near"} industry benchmark 
           for high-performing organizations.
        
        3. **Organizational Alignment:** {"Significant" if duplicate_count > 5 else "Some" if duplicate_count > 0 else "No"} metric duplication 
           across departments {f"({duplicate_count} instances)" if duplicate_count > 0 else ""} indicates 
           {"siloed measurement practices requiring standardization" if duplicate_count > 0 else "good cross-functional alignment"}.
        """)
        
        # Detailed Analysis Section
        st.subheader("Detailed Analysis")
        
        # Analysis of High-Impact Metrics - McKinsey style
        st.markdown("### High-Impact Metrics Analysis")
        
        if len(top_metrics_df) > 0:
            st.markdown("""
            These strategic metrics represent your organization's critical KPIs that directly inform business 
            decisions and demonstrate clear ROI. They drive operational excellence, strategic decision-making, 
            and create measurable business value.
            
            **Impact assessment factors:**
            
            1. **Decision-making integration:** Metrics directly informing tactical and strategic decisions
            2. **Organizational visibility:** Level of cross-functional awareness and executive sponsorship
            3. **Measurement cadence:** Frequency of review and use in operational processes
            4. **Strategic alignment:** Direct connection to corporate objectives and value creation
            """)
            
            # Display high-impact metrics with detailed consulting analysis
            for idx, row in top_metrics_df.iterrows():
                with st.expander(f"{row['Department']} - {row['Metric_Name']} (Score: {row['Score']*10:.1f}/10)"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown(f"**Department:** {row['Department']}")
                        st.markdown(f"**Value Score:** {(row['Score']*10):.1f}/10")
                        
                        # Generate justification based on data with more consultant language
                        justifications = []
                        if row["Used_in_Decision_Making"]:
                            justifications.append("✓ **Active Decision Support:** Directly informs business decisions and operational strategies")
                        
                        if "tied to real goals" in row["Interpretation_Notes"].lower():
                            justifications.append("✓ **Strategic Alignment:** Cascades from corporate objectives to operational execution")
                        
                        if row["Last_Reviewed"] in ["This week", "Last month"]:
                            justifications.append(f"✓ **Regular Cadence:** Maintains current relevance ({row['Last_Reviewed'].lower()})")
                        
                        if row["Metric_Last_Used_For_Decision"] in ["Recently", "2 weeks ago", "Used in QBR"]:
                            justifications.append(f"✓ **Proven Utility:** Recently leveraged for business decisions ({row['Metric_Last_Used_For_Decision']})")
                        
                        if row["Executive_Requested"]:
                            justifications.append("✓ **Executive Visibility:** Receives leadership attention and sponsorship")
                        
                        # Add any specific notes from the interpretation
                        if len(justifications) > 0:
                            st.markdown("**Value Drivers:**")
                            for j in justifications:
                                st.markdown(j)
                        
                        # Business context and stakeholder implications
                        st.markdown("**Business Context:**")
                        
                        # Dynamically generate business context based on the metric properties
                        if "revenue" in row["Metric_Name"].lower() or "churn" in row["Metric_Name"].lower():
                            st.markdown("This financial performance indicator directly impacts P&L forecasting and investor relations narratives.")
                        elif "customer" in row["Metric_Name"].lower() or "user" in row["Metric_Name"].lower():
                            st.markdown("Customer-centric metric with implications for product strategy, retention initiatives, and growth forecasting.")
                        elif "bug" in row["Metric_Name"].lower() or "crash" in row["Metric_Name"].lower():
                            st.markdown("Quality assurance indicator affecting brand perception, customer satisfaction, and support resource allocation.")
                        else:
                            st.markdown("Cross-functional indicator with stakeholder implications across multiple business functions.")
                        
                        st.markdown(f"**Notes:** {row['Interpretation_Notes']}")
                    
                    # Add a metric health indicator in the second column
                    with col2:
                        # Calculate health score based on various factors (0-100)
                        health_score = 0
                        if row["Used_in_Decision_Making"]:
                            health_score += 30
                        if row["Executive_Requested"]:
                            health_score += 15
                        if row["Visible_in_Dashboard"]:
                            health_score += 10
                        if row["Last_Reviewed"] in ["This week"]:
                            health_score += 25
                        elif row["Last_Reviewed"] in ["Last month"]:
                            health_score += 15
                        if row["Metric_Last_Used_For_Decision"] in ["Recently"]:
                            health_score += 20
                        elif row["Metric_Last_Used_For_Decision"] in ["2 weeks ago", "Used in QBR"]:
                            health_score += 10
                        
                        # Show health gauge
                        if health_score >= 80:
                            st.markdown("#### Metric Health: Excellent")
                            st.progress(health_score/100)
                            st.markdown("**Maintain & Leverage**")
                        elif health_score >= 60:
                            st.markdown("#### Metric Health: Good")
                            st.progress(health_score/100)
                            st.markdown("**Optimize & Enhance**")
                        else:
                            st.markdown("#### Metric Health: Needs Attention")
                            st.progress(health_score/100)
                            st.markdown("**Requires Intervention**")
            
            # General recommendations for high-impact metrics
            st.markdown("### High-Impact Metrics Recommendations")
            st.markdown("""
            To maximize the value of your high-impact metrics:
            
            * Establish clear ownership for each high-impact metric
            * Document data sources, collection methodology, and calculation formulas
            * Map each metric to specific business decisions it informs
            * Create standardized reporting templates with actionable insights
            * Ensure consistent review cadences for these mission-critical measures
            """)
        else:
            st.warning("""
            No high-impact metrics were identified. This could indicate:
            
            1. Metrics aren't being actively used for decision-making
            2. The connection between metrics and business outcomes isn't clear
            3. The organization may be collecting data without actionable purpose
            
            Consider a deeper review of how metrics inform business decisions.
            """)
        
        # Analysis of Vanity Metrics
        st.markdown("### Vanity Metrics Analysis")
        
        if len(vanity_metrics_df) > 0:
            st.markdown("""
            Our analysis identified the following metrics as demonstrating limited business value.
            These KPIs have minimal connection to decision-making while consuming organizational resources.
            
            **Limited value indicators:**
            
            1. **Business impact assessment:** Limited correlation with business outcomes
            2. **Decision utility:** Low integration with critical business decisions
            3. **Review frequency:** Infrequent evaluation and usage in business processes
            4. **Organizational momentum:** Metrics that persist due to historical precedent rather than current value
            """)
            
            # Display top vanity metrics with consultant-style justification
            for idx, row in vanity_metrics_df.iterrows():
                with st.expander(f"{row['Department']} - {row['Metric_Name']} (Score: {row['Score']*10:.1f}/10)"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown(f"**Department:** {row['Department']}")
                        st.markdown(f"**Value Score:** {(row['Score']*10):.1f}/10")
                        
                        # Generate justification based on data with consulting terminology
                        reasons = []
                        if not row["Used_in_Decision_Making"]:
                            reasons.append("✗ **Decision Disconnection:** Not integrated into operational or strategic decision processes")
                        
                        if "vanity" in row["Interpretation_Notes"].lower():
                            reasons.append("✗ **Perception-Focused:** Oriented toward appearance rather than substantive business value")
                        
                        if "optics" in row["Interpretation_Notes"].lower():
                            reasons.append("✗ **Stakeholder Theater:** Maintained primarily for impression management rather than business intelligence")
                        
                        if row["Last_Reviewed"] in ["Unknown", "Last quarter"]:
                            reasons.append(f"✗ **Review Deficit:** Inadequate cadence of critical evaluation ({row['Last_Reviewed']})")
                        
                        if row["Metric_Last_Used_For_Decision"] in ["Never", "Don't know"]:
                            reasons.append(f"✗ **Utility Gap:** No documented instances of decision application ({row['Metric_Last_Used_For_Decision']})")
                        
                        # Add any specific notes from the interpretation
                        if len(reasons) > 0:
                            st.markdown("**Value Inhibitors:**")
                            for r in reasons:
                                st.markdown(r)
                        
                        # Insufficient information disclaimer if needed
                        if len(reasons) <= 1:
                            st.markdown("""
                            **Information Sufficiency Assessment:** Limited contextual data available. 
                            Classification is probabilistic and warrants targeted investigation with key stakeholders.
                            """)
                        
                        st.markdown(f"**Context Notes:** {row['Interpretation_Notes']}")
                    
                    # Add a recommendation section in the second column
                    with col2:
                        st.markdown("#### Recommended Action")
                        
                        # Determine recommendation based on score and properties
                        score = row["Score"]
                        if score < 0.2:
                            st.error("**Eliminate**")
                            st.markdown("Consider removal from reporting ecosystem")
                        elif score < 0.4:
                            st.warning("**Deprioritize**")
                            st.markdown("Relocate to secondary dashboards with reduced refresh frequency")
                        else:
                            st.info("**Transform**")
                            st.markdown("Candidate for redefinition with clearer decision-making application")
            
            # General recommendations for vanity metrics
            st.markdown("### Vanity Metrics Recommendations")
            st.markdown("""
            **General recommendations for low-value metrics:**
                
            * Evaluate each metric against clear business objectives
            * Consult stakeholders before removing any established metric
            * Consider consolidating similar metrics into more meaningful composites
            * Transition focus to metrics that directly inform business decisions
            * Document rationale for any metric retirements or transformations
            """)
        
        # Duplicated Metrics Analysis - McKinsey style cross-functional optimization
        if duplicate_metrics:
            st.markdown("### Organizational Alignment Assessment")
            
            # Count actual duplicates for analysis
            true_duplicates = [metric for metric, depts in duplicate_metrics.items() if len(depts) > 1]
            duplicate_count = len(true_duplicates)
            
            st.markdown(f"""
            Our cross-functional analysis identified **{duplicate_count} metrics** being tracked independently across 
            multiple departments. This pattern of metric fragmentation typically indicates structural challenges in 
            enterprise measurement governance:
            """)
            
            # Create metrics for duplicate impact
            col1, col2, col3 = st.columns(3)
            
            # Metric 1: Duplication count
            col1.metric(
                "Duplicate Metrics", 
                f"{duplicate_count}",
                help="Number of metrics duplicated across multiple departments"
            )
            
            # Metric 2: Most fragmented metric
            if duplicate_metrics:
                most_duplicated = max(duplicate_metrics.items(), key=lambda x: len(x[1]) if isinstance(x[1], list) else 0)
                most_duplicated_metric = most_duplicated[0]
                duplicate_count = len(most_duplicated[1])
                col2.metric(
                    "Most Fragmented Metric", 
                    most_duplicated_metric,
                    help="The metric with the highest degree of duplication across departments"
                )
            
            # Metric 3: Data inconsistency risk
            # Determine risk level based on duplication count
            if duplicate_metrics:
                # Simple risk calculation based on duplicate counts
                if duplicate_count > 5:
                    risk_level = "High"
                elif duplicate_count > 2:
                    risk_level = "Medium"
                else:
                    risk_level = "Low"
                    
                col3.metric(
                    "Alignment Risk Level", 
                    risk_level,
                    help="Assessment of potential data inconsistency and decision misalignment"
                )
            
            # Root cause analysis
            st.markdown("""
            #### Root Cause Analysis
            
            Cross-functional metric duplication typically stems from three primary organizational patterns:
            
            1. **Governance Fragmentation:** Absence of centralized KPI definition and ownership framework
            2. **System Proliferation:** Multiple reporting tools and data sources without integration
            3. **Functional Isolation:** Departments optimizing for local visibility without enterprise architecture
            """)
            
            # Show the duplicate metrics with more structured presentation
            with st.expander("Detailed Fragmentation Map"):
                if len(true_duplicates) > 0:
                    for metric in true_duplicates:
                        depts = duplicate_metrics[metric]
                        dept_count = len(depts)
                        
                        # Create a visual representation of the duplication
                        col1, col2 = st.columns([1, 3])
                        
                        # Left column - Metric name and count
                        with col1:
                            st.markdown(f"**{metric}**")
                            st.caption(f"{dept_count} departments")
                        
                        # Right column - Departments as "badges"
                        with col2:
                            # Create a horizontal layout of department badges
                            html_badges = ""
                            for dept in depts:
                                badge_color = "#3498db"  # Default blue
                                html_badges += f"""
                                <span style="
                                    display: inline-block;
                                    padding: 5px 10px;
                                    margin: 3px;
                                    background-color: {badge_color};
                                    color: white;
                                    border-radius: 10px;
                                    font-size: 0.8em;
                                ">
                                    {dept}
                                </span>
                                """
                            st.markdown(html_badges, unsafe_allow_html=True)
                        
                        # Add a divider between metrics
                        st.markdown("---")
            
            # Business impact analysis with improved readability
            st.markdown("#### Business Impact Assessment")
            st.markdown("Metric fragmentation introduces several enterprise risks and opportunity costs:")
            
            # Creating a custom styled table with better contrast
            impact_data = [
                ["Data Integrity", "Inconsistent definitions and calculation methodologies", "High"],
                ["Decision Alignment", "Departments using different values for same business concept", "High"],
                ["Resource Efficiency", "Duplicate data collection, validation, and reporting effort", "Medium"],
                ["Analytics Effectiveness", "Analytical resources spread across redundant metrics", "Medium"],
                ["Organizational Trust", "Stakeholder confusion and credibility challenges", "High"]
            ]
            
            # Create DataFrame for display
            impact_df = pd.DataFrame(
                impact_data, 
                columns=["Impact Area", "Implications", "Risk Level"]
            )
            
            # Display as styled DataFrame with good contrast
            st.dataframe(
                impact_df,
                use_container_width=True,
                hide_index=True
            )
            
            # Recommendations for metric duplication
            st.markdown("#### Recommendations for Metric Duplication")
            
            st.markdown("""
            To address metric duplication across departments:
            
            * Establish a single source of truth for each business concept
            * Standardize definitions and calculation methodologies
            * Implement cross-functional metric ownership
            * Create a centralized metrics dictionary
            * Consolidate reporting to ensure consistent visibility
            """)
        
        # Strategic Recommendations
        st.subheader("Strategic Recommendations")
        
        st.markdown("""
        Based on our comprehensive analysis of your organization's measurement ecosystem, we recommend 
        focusing on the following key areas:
        
        1. **Metric Rationalization:** Focus your resources on the high-impact metrics identified while 
           reducing emphasis on metrics with limited decision-making utility
           
        2. **Standardization:** Establish consistent definitions, ownership, and review cadences for 
           your critical metrics
           
        3. **Alignment:** Create clear connections between metrics and business objectives to ensure 
           all measurement directly supports organizational goals
           
        4. **Governance:** Implement a formal review process to continuously evaluate metric relevance 
           and effectiveness
        """)
        
    # Tab 2: Visualizations Tab
    with tab2:
        st.header("Metric Visualizations")
        
        st.subheader("Metrics Classification Overview")
        # Create two columns for the visualizations with equal width
        viz_col1, viz_col2 = st.columns([1, 1])
        
        with viz_col1:
            # Classification Breakdown Visualization
            fig1 = create_key_metrics_breakdown(analysis_df)
            # Use fixed height and width instead of container width
            st.plotly_chart(fig1, use_container_width=False)
        
        with viz_col2:
            # Department Metrics Visualization
            fig2 = create_metrics_by_department(analysis_df)
            # Use fixed height and width instead of container width
            st.plotly_chart(fig2, use_container_width=False)
        
        # High Impact Metrics Table
        st.subheader("High Impact Metrics")
        if len(top_metrics_df) > 0:
            # Create a more consistent table display
            high_impact_table = top_metrics_df[["Department", "Metric_Name", "Score"]].copy()
            high_impact_table.columns = ["Department", "Metric", "Value Score"]
            # Format score on 0-10 scale
            high_impact_table["Value Score"] = (high_impact_table["Value Score"] * 10).round(1)
            # Use dataframe display instead of HTML
            st.dataframe(high_impact_table, use_container_width=True)
        else:
            st.info("No high-impact metrics identified based on current filters and threshold.")
        
        # Vanity Metrics Table with more details
        st.subheader("Top Vanity Metrics")
        if len(vanity_metrics_df) > 0:
            vanity_table = vanity_metrics_df[["Department", "Metric_Name", "Score", "Interpretation_Notes"]].copy()
            vanity_table.columns = ["Department", "Metric", "Value Score", "Notes"]
            # Convert score to 0-10 scale instead of percentage
            vanity_table["Value Score"] = (vanity_table["Value Score"] * 10).round(1)
            
            st.dataframe(vanity_table, use_container_width=True)
        else:
            st.info("No vanity metrics found with current filters.")
    
    # Tab 3: Metrics Details (original tab2 content)
    with tab3:
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
            
            if st.button("Export Analysis"):
                # Prepare export dataframe
                export_df = analysis_df[["Department", "Metric_Name", "Visible_in_Dashboard", 
                                       "Used_in_Decision_Making", "Executive_Requested", 
                                       "Last_Reviewed", "Metric_Last_Used_For_Decision",
                                       "Score", "Classification", "Interpretation_Notes"]]
                
                csv = export_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name="kpi_audit_results.csv",
                    mime="text/csv",
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
                    st.markdown(f"**Value Score:** {(metric_data['Score'] * 10):.1f}/10")
                    
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