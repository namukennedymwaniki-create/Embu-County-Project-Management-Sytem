"""
Dashboard — Embu County Project Management System
Displays project KPIs, filters, and subcounty/ward breakdowns.
"""

import streamlit as st
from utils.db import run_query

def render():
    st.title("🏗️ Project Implementation Dashboard")
    st.caption("Embu County Government — Land of Opportunities")
    st.markdown("---")

    try:
        projects = run_query("""
            SELECT
                p.id, p.project_name, p.contract_sum, p.project_status, p.remarks,
                s.name AS subcounty, w.name AS ward, d.name AS department
            FROM projects p
            LEFT JOIN subcounties s ON p.subcounty_id = s.id
            LEFT JOIN wards w ON p.ward_id = w.id
            LEFT JOIN departments d ON p.department_id = d.id
            ORDER BY p.id DESC
        """)
    except Exception as e:
        st.error(f"⚠️ Could not load projects: {e}")
        return
# =====================================================
# HEADER
# =====================================================
st.title("🏗️ Project Implementation Dashboard")
st.caption("Embu County Government — Land of Opportunities")
st.markdown("---")

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
# INLINE FILTERS (in main area, not sidebar)
# =====================================================
with st.expander("🔎 Filters", expanded=True):
    col1, col2, col3 = st.columns(3)

    subcounty_options = sorted(projects['subcounty'].dropna().unique().tolist()) \
        if not projects.empty else []
    selected_subcounties = col1.multiselect(
        "Subcounty", options=subcounty_options, default=subcounty_options,
        key="filter_subcounty",
    )

    status_options = ["Not Started", "In Progress", "Completed", "Stalled", "Cancelled"]
    selected_status = col2.multiselect(
        "Project Status", options=status_options, default=status_options,
        key="filter_status",
    )

    department_options = sorted(projects['department'].dropna().unique().tolist()) \
        if not projects.empty else []
    selected_departments = col3.multiselect(
        "Department", options=department_options, default=department_options,
        key="filter_department",
    )

    if st.button("🔄 Refresh Data"):
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

c1, c2, c3, c4 = st.columns(4)
c1.metric("📋 Total Projects", f"{total_projects:,}")
c2.metric("💰 Total Contract Sum", f"KES {total_value:,.0f}")
c3.metric("✅ Completed", f"{completed:,}")
c4.metric("🚧 In Progress", f"{in_progress:,}")

st.markdown("---")

# =====================================================
# SUBCounty SUMMARY
# =====================================================
st.subheader("📍 Projects by Subcounty")

if not filtered.empty:
    subcounty_summary = (
        filtered.groupby('subcounty')
        .agg(project_count=('id', 'count'), total_value=('contract_sum', 'sum'))
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
            subcounty_summary, use_container_width=True, hide_index=True,
            column_config={
                "Total Contract Sum (KES)": st.column_config.NumberColumn(format="KES %,.0f"),
            },
        )
    with col_b:
        st.bar_chart(
            subcounty_summary.set_index('Subcounty')['Projects'],
            use_container_width=True, height=250,
        )
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
        .agg(project_count=('id', 'count'), total_value=('contract_sum', 'sum'))
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
        ward_summary, use_container_width=True, hide_index=True,
        column_config={
            "Total Contract Sum (KES)": st.column_config.NumberColumn(format="KES %,.0f"),
        },
    )
else:
    st.info("No ward-level data available.")

st.markdown("---")

# =====================================================
# STATUS OVERVIEW
# =====================================================
st.subheader("📊 Project Status Overview")

if not filtered.empty:
    status_summary = (
        filtered.groupby('project_status')
        .agg(project_count=('id', 'count'), total_value=('contract_sum', 'sum'))
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
            status_summary, use_container_width=True, hide_index=True,
            column_config={
                "Total Contract Sum (KES)": st.column_config.NumberColumn(format="KES %,.0f"),
            },
        )
    with col_d:
        st.bar_chart(
            status_summary.set_index('Status')['Projects'],
            use_container_width=True, height=250,
        )
else:
    st.info("No status data available.")

st.markdown("---")

# =====================================================
# RECENT PROJECTS
# =====================================================
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
        recent, use_container_width=True, hide_index=True,
        column_config={
            "Contract Sum (KES)": st.column_config.NumberColumn(format="KES %,.0f"),
        },
    )
else:
    st.info("No projects to display. Head over to the **Projects** page to add one.")

st.markdown("---")
st.caption("© Embu County Government · Project Management System · Land of Opportunities")
