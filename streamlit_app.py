import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
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

# Run the main application
import app