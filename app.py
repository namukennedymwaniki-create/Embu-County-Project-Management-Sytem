import streamlit as st
import pandas as pd
from utils.db import run_query

st.set_page_config(page_title="County Projects Dashboard", layout="wide")

st.title("🏗️ County Project Implementation Dashboard")

# Load data
projects = run_query("""
    SELECT p.*, s.name as subcounty, w.name as ward, d.name as department
    FROM projects p
    LEFT JOIN subcounties s ON p.subcounty_id = s.id
    LEFT JOIN wards w ON p.ward_id = w.id
    LEFT JOIN departments d ON p.department_id = d.id
""")

# Sidebar filters
st.sidebar.header("Filters")
selected_subcounties = st.sidebar.multiselect(
    "Subcounty", 
    options=sorted(projects['subcounty'].dropna().unique()),
    default=sorted(projects['subcounty'].dropna().unique())
)
selected_status = st.sidebar.multiselect(
    "Project Status",
    options=sorted(projects['project_status'].unique()),
    default=sorted(projects['project_status'].unique())
)

# Apply filters
filtered = projects[
    (projects['subcounty'].isin(selected_subcounties)) &
    (projects['project_status'].isin(selected_status))
]

# KPI metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Projects", len(filtered))
col2.metric("Total Contract Sum", f"KES {filtered['contract_sum'].sum():,.0f}")
col3.metric("Completed", len(filtered[filtered['project_status'] == 'Completed']))
col4.metric("In Progress", len(filtered[filtered['project_status'] == 'In Progress']))

# Subcounty breakdown
st.subheader("Projects by Subcounty")
subcounty_summary = filtered.groupby('subcounty').agg(
    project_count=('id', 'count'),
    total_value=('contract_sum', 'sum')
).reset_index()
st.dataframe(subcounty_summary, use_container_width=True)

# Ward-level view
st.subheader("Ward-Level Project Distribution")
ward_summary = filtered.groupby(['subcounty', 'ward']).agg(
    project_count=('id', 'count'),
    total_value=('contract_sum', 'sum')
).reset_index()
st.dataframe(ward_summary, use_container_width=True)
