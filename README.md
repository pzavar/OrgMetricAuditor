# KPI Audit Tool

A data-driven tool that analyzes organizational metrics to identify high-value KPIs and eliminate vanity metrics.

**Website URL**: [https://metric-auditor.streamlit.app/](https://metric-auditor.streamlit.app/)

## What it Does

- Analyzes metrics across departments
- Identifies which metrics drive real decisions vs vanity metrics
- Provides interactive visualizations and scoring
- Helps reduce wasted effort on tracking meaningless data

## Using the Tool

1. Upload your metrics CSV or use sample data
2. View analysis across:
   - Interactive metric scoring dashboard
   - Department-level breakdowns  
   - Individual metric deep-dives

## Data Format

Your CSV should include these columns:

```
Department,Metric_Name,Visible_in_Dashboard,Used_in_Decision_Making,Executive_Requested,Last_Reviewed,Metric_Last_Used_For_Decision,Interpretation_Notes
```

Sample templates are available in the tool for both full and minimal datasets.

## Key Features

- **Automated Metric Classification**: Sophisticated algorithm to identify high-impact vs. vanity metrics
- **Interactive Visualizations**: Rich, interactive charts powered by Plotly
- **Department-Level Analysis**: Cross-functional metric analysis to identify silos and redundancies
- **Value Factor Analysis**: Multi-dimensional scoring based on actual usage, decision-making impact, and review frequency
- **Actionable Insights**: Clear recommendations for metric optimization
- **Data Export**: Export analysis results in CSV or Excel format


## Key Components

- `app.py`: Main application and UI logic
- `analysis.py`: Core metric analysis algorithms
- `visualization.py`: Data visualization components
- `utils.py`: Helper functions and data preprocessing

## Technical Stack

- **Frontend**: Streamlit
- **Data Analysis**: Pandas, NumPy
- **Visualization**: Plotly Express, Plotly Graph Objects
- **Export Capabilities**: CSV, Excel

## Business Impact

- Identify metrics that truly drive business decisions
- Reduce resources spent on low-value metrics
- Improve cross-functional metric alignment
- Optimize dashboard real estate
- Drive data-driven decision making

## Example Analysis

The tool provides:
- Executive summary of metric ecosystem health
- Detailed analysis of high-impact metrics
- Identification of potential vanity metrics
- Cross-departmental metric duplication analysis
- Actionable recommendations for optimization

## Contributing

Feel free to open issues or submit pull requests. We welcome contributions to enhance the tool's capabilities.

## License

MIT License - feel free to use and modify as needed.