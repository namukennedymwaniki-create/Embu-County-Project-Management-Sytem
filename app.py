"""
Embu County Project Management System
Main Dashboard Page
"""

import streamlit as st
import pandas as pd
import base64
from pathlib import Path
from utils.db import run_query

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Embu County PMS",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =====================================================
# SIDEBAR HEADER - Embu County branding
# =====================================================
# Load logo as base64 for reliable rendering
logo_b64 = ""
logo_path = Path("assets/embu_logo.png")
if logo_path.exists():
    logo_b64 = base64.b64encode(logo_path.read_bytes()).decode()

with st.sidebar:
    if logo_b64:
        st.markdown(f"""
            <div style="
                text-align: center;
                padding: 20px 12px;
                margin-bottom: 24px;
                background: rgba(255,255,255,0.06);
                border-radius: 16px;
                border: 1px solid rgba(255,255,255,0.08);
            ">
                <div style="
                    width: 72px;
                    height: 72px;
                    background: white;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0 auto 12px auto;
                    box-shadow: 0 4px 12px rgba(212,175,55,0.35);
                    overflow: hidden;
                    padding: 6px;
                ">
                    <img src="data:image/png;base64,{logo_b64}"
                         style="width: 100%; height: 100%; object-fit: contain;" />
                </div>
                <div style="font-size: 16px; font-weight: 700; color: white; letter-spacing: 0.5px;">
                    EMBU COUNTY
                </div>
                <div style="font-size: 12px; font-weight: 600; color: #eab308; margin-top: 4px;">
                    Project Management System
                </div>
                <div style="font-size: 10px; color: #94a3b8; margin-top: 8px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.05);">
                    Land of Opportunities
                </div>
            </div>
        """, unsafe_allow_html=True)
    else:
        # Fallback if logo file not found
        st.markdown("""
            <div style="text-align: center; padding: 20px 12px; margin-bottom: 24px;
                        background: rgba(255,255,255,0.06); border-radius: 16px;
                        border: 1px solid rgba(255,255,255,0.08);">
                <div style="font-size: 32px;">🏛️</div>
                <div style="font-size: 16px; font-weight: 700; color: white; letter-spacing: 0.5px; margin-top: 8px;">
                    EMBU COUNTY
                </div>
                <div style="font-size: 12px; font-weight: 600; color: #eab308; margin-top: 4px;">
                    Project Management System
                </div>
            </div>
        """, unsafe_allow_html=True)

# =====================================================
# LOAD DATA
# =====================================================
try:
    projects = run_query("""
        SELECT
            p.id,
            p.project_name,
            p.contract_sum,
            p.project_status,
            p.remarks,
            s.name AS subcounty,
            w.name AS ward,
            d.name AS department
        FROM projects p
        LEFT JOIN subcounties s ON p.subcounty_id = s.id
        LEFT JOIN wards w ON p.ward_id = w.id
        LEFT JOIN departments d ON p.department_id = d.id
        ORDER BY p.id DESC
    """)
except Exception as e:
    st.error(f"⚠️ Could not load projects from the database: {e}")
    st.stop()

# =====================================================
# MAIN HEADER
# =====================================================
st.title("🏗️ Project Implementation Dashboard")
st.caption("Embu County Government — Land of Opportunities")
st.markdown("---")

# =====================================================
# SIDEBAR FILTERS
# =====================================================
with st.sidebar:
    st.markdown("### 🔎 Filters")

    subcounty_options = sorted(projects['subcounty'].dropna().unique().tolist()) \
        if not projects.empty else []
    selected_subcounties = st.multiselect(
        "Subcounty",
        options=subcounty_options,
        default=subcounty_options,
        key="filter_subcounty",
    )

    status_options = ["Not Started", "In Progress", "Completed", "Stalled", "Cancelled"]
    selected_status = st.multiselect(
        "Project Status",
        options=status_options,
        default=status_options,
        key="filter_status",
    )

    department_options = sorted(projects['department'].dropna().unique().tolist()) \
        if not projects.empty else []
    selected_departments = st.multiselect(
        "Department",
        options=department_options,
        default=department_options,
        key="filter_department",
    )

    st.markdown("---")
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# =====================================================
# APPLY FILTERS
# =====================================================
if projects.empty:
    filtered = projects.copy()
else:
    filtered = projects[
        (projects['subcounty'].isin(selected_subcounties)) &
        (projects['project_status'].isin(selected_status)) &
        (projects['department'].isin(selected_departments))
    ]

# =====================================================
# KPI METRICS
# =====================================================
total_projects = len(filtered)
total_value = filtered['contract_sum'].sum() if not filtered.empty else 0
completed = len(filtered[filtered['project_status'] == 'Completed']) if not filtered.empty else 0
in_progress = len(filtered[filtered['project_status'] == 'In Progress']) if not filtered.empty else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("📋 Total Projects", f"{total_projects:,}")
col2.metric("💰 Total Contract Sum", f"KES {total_value:,.0f}")
col3.metric("✅ Completed", f"{completed:,}")
col4.metric("🚧 In Progress", f"{in_progress:,}")

st.markdown("---")

# =====================================================
# SUBCounty SUMMARY
# =====================================================
st.subheader("📍 Projects by Subcounty")

if not filtered.empty:
    subcounty_summary = (
        filtered.groupby('subcounty')
        .agg(
            project_count=('id', 'count'),
            total_value=('contract_sum', 'sum'),
        )
        .reset_index()
        .rename(columns={
            'subcounty': 'Subcounty',
            'project_count': 'Projects',
            'total_value': 'Total Contract Sum (KES)',
        })
        .sort_values('Projects', ascending=False)
    )

    col_a, col_b = st.columns([2, 1])

    with col_a:
        st.dataframe(
            subcounty_summary,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Total Contract Sum (KES)": st.column_config.NumberColumn(
                    format="KES %,.0f"
                ),
            },
        )

    with col_b:
        chart_data = subcounty_summary.set_index('Subcounty')['Projects']
        st.bar_chart(chart_data, use_container_width=True, height=250)
else:
    st.info("No projects match the current filters.")

st.markdown("---")

# =====================================================
# WARD-LEVEL BREAKDOWN
# =====================================================
st.subheader("🗺️ Ward-Level Project Distribution")

if not filtered.empty:
    ward_summary = (
        filtered.groupby(['subcounty', 'ward'])
        .agg(
            project_count=('id', 'count'),
            total_value=('contract_sum', 'sum'),
        )
        .reset_index()
        .rename(columns={
            'subcounty': 'Subcounty',
            'ward': 'Ward',
            'project_count': 'Projects',
            'total_value': 'Total Contract Sum (KES)',
        })
        .sort_values(['Subcounty', 'Ward'])
    )

    st.dataframe(
        ward_summary,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Total Contract Sum (KES)": st.column_config.NumberColumn(
                format="KES %,.0f"
            ),
        },
    )
else:
    st.info("No ward-level data available for the current filters.")

st.markdown("---")

# =====================================================
# PROJECT STATUS BREAKDOWN
# =====================================================
st.subheader("📊 Project Status Overview")

if not filtered.empty:
    status_summary = (
        filtered.groupby('project_status')
        .agg(
            project_count=('id', 'count'),
            total_value=('contract_sum', 'sum'),
        )
        .reset_index()
        .rename(columns={
            'project_status': 'Status',
            'project_count': 'Projects',
            'total_value': 'Total Contract Sum (KES)',
        })
    )

    col_c, col_d = st.columns([1, 1])

    with col_c:
        st.dataframe(
            status_summary,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Total Contract Sum (KES)": st.column_config.NumberColumn(
                    format="KES %,.0f"
                ),
            },
        )

    with col_d:
        status_chart = status_summary.set_index('Status')['Projects']
        st.bar_chart(status_chart, use_container_width=True, height=250)
else:
    st.info("No status data available.")

# =====================================================
# RECENT PROJECTS TABLE
# =====================================================
st.markdown("---")
st.subheader("🕒 Recent Projects")

if not filtered.empty:
    recent = filtered.head(10)[
        ['project_name', 'subcounty', 'ward', 'department',
         'contract_sum', 'project_status', 'remarks']
    ].rename(columns={
        'project_name': 'Project Name',
        'subcounty': 'Subcounty',
        'ward': 'Ward',
        'department': 'Department',
        'contract_sum': 'Contract Sum (KES)',
        'project_status': 'Status',
        'remarks': 'Remarks',
    })

    st.dataframe(
        recent,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Contract Sum (KES)": st.column_config.NumberColumn(
                format="KES %,.0f"
            ),
        },
    )
else:
    st.info("No projects to display. Head over to the **Projects** page to add one.")

# =====================================================
# FOOTER
# =====================================================
st.markdown("---")
st.caption(
    "© Embu County Government · Project Management System · "
    "Land of Opportunities"
)
