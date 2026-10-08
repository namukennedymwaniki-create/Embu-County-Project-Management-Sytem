"""
Dashboard view — Embu County Project Management System.
Executive dashboard with KPIs, subcounty insights, and interactive charts.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
from utils.db import run_query


# =====================================================
# THEME / COLORS
# =====================================================
PRIMARY = "#eab308"        # Embu gold
PRIMARY_DARK = "#b45309"   # Dark gold
SUCCESS = "#10b981"        # Green
WARNING = "#f59e0b"        # Amber
DANGER = "#ef4444"         # Red
INFO = "#3b82f6"           # Blue
NEUTRAL = "#64748b"        # Slate
BG_CARD = "#ffffff"
BG_SOFT = "#f8fafc"

STATUS_COLORS = {
    "Completed":   SUCCESS,
    "In Progress": INFO,
    "Not Started": NEUTRAL,
    "Stalled":     WARNING,
    "Cancelled":   DANGER,
}


# =====================================================
# HELPERS
# =====================================================
def _fmt_kes(value):
    """Format number as compact KES (e.g., KES 12.5M)."""
    if value is None or pd.isna(value):
        return "KES 0"
    v = float(value)
    if abs(v) >= 1_000_000_000:
        return f"KES {v/1_000_000_000:.2f}B"
    if abs(v) >= 1_000_000:
        return f"KES {v/1_000_000:.2f}M"
    if abs(v) >= 1_000:
        return f"KES {v/1_000:.1f}K"
    return f"KES {v:,.0f}"


def _fmt_kes_full(value):
    """Format number as full KES with commas."""
    if value is None or pd.isna(value):
        return "KES 0"
    return f"KES {float(value):,.0f}"


def _kpi_card(label, value, delta=None, icon="", color=PRIMARY):
    """Render a professional KPI card."""
    delta_html = ""
    if delta is not None:
        delta_color = SUCCESS if delta >= 0 else DANGER
        arrow = "▲" if delta >= 0 else "▼"
        delta_html = (
            f'<div style="color:{delta_color}; font-size:13px; '
            f'font-weight:600; margin-top:6px;">'
            f'{arrow} {abs(delta):.1f}%</div>'
        )

    st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border: 1px solid #e2e8f0;
            border-left: 4px solid {color};
            border-radius: 12px;
            padding: 20px 22px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
            height: 100%;
        ">
            <div style="display:flex; justify-content:space-between;
                        align-items:center; margin-bottom:8px;">
                <div style="font-size:12px; font-weight:600; color:#64748b;
                            text-transform:uppercase; letter-spacing:0.5px;">
                    {label}
                </div>
                <div style="font-size:22px;">{icon}</div>
            </div>
            <div style="font-size:28px; font-weight:700; color:#0f172a;
                        line-height:1.1;">
                {value}
            </div>
            {delta_html}
        </div>
    """, unsafe_allow_html=True)


def _status_badge(status):
    """Return an HTML status badge."""
    fg_map = {
        "Completed":    ("#065f46", "#d1fae5"),
        "In Progress":  ("#1e40af", "#dbeafe"),
        "Not Started":  ("#374151", "#e5e7eb"),
        "Stalled":      ("#92400e", "#fef3c7"),
        "Cancelled":    ("#991b1b", "#fee2e2"),
    }
    fg, bg = fg_map.get(status, ("#374151", "#e5e7eb"))
    return (
        f'<span style="background:{bg}; color:{fg}; padding:4px 12px; '
        f'border-radius:12px; font-size:12px; font-weight:600;">'
        f'{status}</span>'
    )


def _style_plotly(fig, height=340):
    """Apply a consistent professional style to Plotly figures."""
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=30, b=10),
        font=dict(family="Inter, -apple-system, sans-serif", size=12,
                  color="#334155"),
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=False,
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Inter, sans-serif",
        ),
    )
    fig.update_xaxes(showgrid=False, linecolor="#e2e8f0")
    fig.update_yaxes(gridcolor="#f1f5f9", linecolor="#e2e8f0")
    return fig


# =====================================================
# MAIN RENDER
# =====================================================
def render():
    # ---- Load data ----
    try:
        projects = run_query("""
            SELECT
                p.id,
                p.project_name,
                p.contract_sum,
                p.total_funding,
                p.total_expenditure,
                p.percentage_completion,
                p.project_status,
                p.commencement_date,
                p.expected_completion_date,
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
        st.error(f"⚠️ Could not load projects: {e}")
        return

    # =====================================================
    # PAGE HEADER
    # =====================================================
    st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            border-radius: 16px;
            padding: 28px 32px;
            margin-bottom: 24px;
            border-left: 6px solid {PRIMARY};
        ">
            <div style="display:flex; justify-content:space-between;
                        align-items:center; flex-wrap:wrap; gap:16px;">
                <div>
                    <div style="font-size:12px; color:{PRIMARY};
                                font-weight:700; letter-spacing:1.5px;
                                text-transform:uppercase;">
                        EMBU COUNTY GOVERNMENT
                    </div>
                    <div style="font-size:28px; color:white; font-weight:700;
                                margin-top:6px; line-height:1.2;">
                        Project Implementation Dashboard
                    </div>
                    <div style="font-size:13px; color:#94a3b8; margin-top:6px;">
                        Land of Opportunities · {date.today().strftime('%d %B %Y')}
                    </div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:11px; color:#64748b;
                                letter-spacing:1px;">
                        LAST REFRESHED
                    </div>
                    <div style="font-size:14px; color:white;
                                font-weight:600; margin-top:4px;">
                        {date.today().strftime('%d %b %Y')}
                    </div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    if projects.empty:
        st.info("📭 No projects yet. Head to the **Projects** module to add some.")
        return

    # =====================================================
    # FILTER BAR
    # =====================================================
    with st.container(border=True):
        st.markdown(
            "<div style='font-size:12px; font-weight:600; color:#64748b; "
            "text-transform:uppercase; letter-spacing:0.5px; "
            "margin-bottom:10px;'>🎛️ Quick Filters</div>",
            unsafe_allow_html=True,
        )

        fc1, fc2, fc3, fc4 = st.columns([1, 1, 1, 1])

        sc_options = ["All Subcounties"] + sorted(
            projects['subcounty'].dropna().unique().tolist()
        )
        sel_sc = fc1.selectbox(
            "Subcounty", sc_options, key="dash_sc_filter"
        )

        if sel_sc == "All Subcounties":
            dept_src = projects['department'].dropna().unique().tolist()
        else:
            dept_src = projects[
                projects['subcounty'] == sel_sc
            ]['department'].dropna().unique().tolist()
        dept_options = ["All Departments"] + sorted(dept_src)
        sel_dept = fc2.selectbox(
            "Department", dept_options, key="dash_dept_filter"
        )

        status_options = ["All Statuses"] + [
            "Completed", "In Progress", "Not Started", "Stalled", "Cancelled"
        ]
        sel_status = fc3.selectbox(
            "Status", status_options, key="dash_status_filter"
        )

        search = fc4.text_input(
            "Search project",
            placeholder="Type name...",
            key="dash_search",
        )

    # ---- Apply filters ----
    filtered = projects.copy()
    if sel_sc != "All Subcounties":
        filtered = filtered[filtered['subcounty'] == sel_sc]
    if sel_dept != "All Departments":
        filtered = filtered[filtered['department'] == sel_dept]
    if sel_status != "All Statuses":
        filtered = filtered[filtered['project_status'] == sel_status]
    if search.strip():
        filtered = filtered[
            filtered['project_name'].str.contains(
                search.strip(), case=False, na=False
            )
        ]

    if filtered.empty:
        st.warning("🔍 No projects match the current filters.")
        return

    # ---- Derived metrics ----
    total_projects = len(filtered)
    total_funding = filtered['total_funding'].fillna(0).sum()
    total_expenditure = filtered['total_expenditure'].fillna(0).sum()
    total_balance = total_funding - total_expenditure
    avg_completion = filtered['percentage_completion'].fillna(0).mean()
    completed_count = len(filtered[filtered['project_status'] == 'Completed'])
    in_progress_count = len(filtered[filtered['project_status'] == 'In Progress'])
    stalled_count = len(filtered[filtered['project_status'] == 'Stalled'])
    absorption_rate = (
        (total_expenditure / total_funding * 100) if total_funding > 0 else 0
    )

    # =====================================================
    # KPI CARDS — ROW 1
    # =====================================================
    st.markdown(
        "<div style='font-size:12px; font-weight:600; color:#64748b; "
        "text-transform:uppercase; letter-spacing:0.5px; margin:18px 0 8px;'>"
        "📊 Portfolio Overview</div>",
        unsafe_allow_html=True,
    )

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        _kpi_card("Total Projects", f"{total_projects:,}",
                  icon="📋", color=INFO)
    with k2:
        _kpi_card("Total Funding", _fmt_kes(total_funding),
                  icon="💰", color=PRIMARY)
    with k3:
        _kpi_card("Total Expenditure", _fmt_kes(total_expenditure),
                  icon="💸", color=WARNING)
    with k4:
        _kpi_card("Avg. Completion", f"{avg_completion:.1f}%",
                  icon="📈", color=SUCCESS)

    # =====================================================
    # KPI CARDS — ROW 2
    # =====================================================
    k5, k6, k7, k8 = st.columns(4)
    with k5:
        _kpi_card("✅ Completed", f"{completed_count:,}",
                  icon="", color=SUCCESS)
    with k6:
        _kpi_card("🚧 In Progress", f"{in_progress_count:,}",
                  icon="", color=INFO)
    with k7:
        _kpi_card("⚠️ Stalled", f"{stalled_count:,}",
                  icon="", color=WARNING)
    with k8:
        _kpi_card("💵 Budget Balance", _fmt_kes(total_balance),
                  icon="", color=PRIMARY_DARK)

    st.markdown("---")

    # =====================================================
    # CHARTS ROW 1 — Subcounty & Status
    # =====================================================
    st.markdown(
        "<div style='font-size:12px; font-weight:600; color:#64748b; "
        "text-transform:uppercase; letter-spacing:0.5px; margin:6px 0 8px;'>"
        "📊 Distribution Analysis</div>",
        unsafe_allow_html=True,
    )

    ch1, ch2 = st.columns([3, 2])

    # ---- Subcounty projects bar ----
    with ch1:
        with st.container(border=True):
            st.markdown("##### 🏘️ Projects by Subcounty")
            sc_summary = (
                filtered.groupby('subcounty')
                .agg(
                    Projects=('id', 'count'),
                    Funding=('total_funding', 'sum'),
                )
                .reset_index()
                .sort_values('Projects', ascending=True)
            )
            fig_sc = px.bar(
                sc_summary, x='Projects', y='subcounty',
                orientation='h',
                color='Projects',
                color_continuous_scale=[[0, "#fef3c7"], [1, PRIMARY]],
                text='Projects',
            )
            fig_sc.update_traces(
                textposition='outside',
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Projects: %{x}<br>"
                    "<extra></extra>"
                ),
            )
            fig_sc.update_layout(coloraxis_showscale=False)
            _style_plotly(fig_sc, height=320)
            st.plotly_chart(fig_sc, use_container_width=True,
                            config={"displayModeBar": False})

    # ---- Status donut ----
    with ch2:
        with st.container(border=True):
            st.markdown("##### 🎯 Project Status")
            status_counts = (
                filtered['project_status'].value_counts().reset_index()
            )
            status_counts.columns = ['Status', 'Count']
            fig_status = go.Figure(data=[go.Pie(
                labels=status_counts['Status'],
                values=status_counts['Count'],
                hole=0.6,
                marker=dict(
                    colors=[
                        STATUS_COLORS.get(s, NEUTRAL)
                        for s in status_counts['Status']
                    ],
                    line=dict(color='white', width=2),
                ),
                textinfo='label+percent',
                textposition='outside',
                hovertemplate="<b>%{label}</b><br>"
                              "Projects: %{value}<br>"
                              "Share: %{percent}<extra></extra>",
            )])
            fig_status.update_layout(
                showlegend=False,
                annotations=[dict(
                    text=f"<b>{total_projects}</b><br>"
                         f"<span style='font-size:11px; color:#64748b'>"
                         f"TOTAL</span>",
                    x=0.5, y=0.5, font_size=20,
                    showarrow=False,
                    font=dict(color="#0f172a"),
                )],
            )
            _style_plotly(fig_status, height=320)
            st.plotly_chart(fig_status, use_container_width=True,
                            config={"displayModeBar": False})

    # =====================================================
    # CHARTS ROW 2 — Department & Financial
    # =====================================================
    ch3, ch4 = st.columns([2, 3])

    # ---- Department breakdown ----
    with ch3:
        with st.container(border=True):
            st.markdown("##### 🏢 Projects by Department")
            dept_summary = (
                filtered.groupby('department')
                .agg(Projects=('id', 'count'))
                .reset_index()
                .sort_values('Projects', ascending=True)
            )
            fig_dept = px.bar(
                dept_summary, x='Projects', y='department',
                orientation='h',
                color='Projects',
                color_continuous_scale=[[0, "#dbeafe"], [1, INFO]],
                text='Projects',
            )
            fig_dept.update_traces(
                textposition='outside',
                hovertemplate="<b>%{y}</b><br>"
                              "Projects: %{x}<extra></extra>",
            )
            fig_dept.update_layout(coloraxis_showscale=False)
            _style_plotly(fig_dept, height=340)
            st.plotly_chart(fig_dept, use_container_width=True,
                            config={"displayModeBar": False})

    # ---- Funding vs Expenditure by subcounty ----
    with ch4:
        with st.container(border=True):
            st.markdown("##### 💰 Funding vs Expenditure by Subcounty")
            fin_summary = (
                filtered.groupby('subcounty')
                .agg(
                    Funding=('total_funding', 'sum'),
                    Expenditure=('total_expenditure', 'sum'),
                )
                .reset_index()
            )
            fig_fin = go.Figure()
            fig_fin.add_trace(go.Bar(
                x=fin_summary['subcounty'],
                y=fin_summary['Funding'],
                name='Total Funding',
                marker_color=PRIMARY,
                hovertemplate="<b>%{x}</b><br>"
                              "Funding: KES %{y:,.0f}<extra></extra>",
            ))
            fig_fin.add_trace(go.Bar(
                x=fin_summary['subcounty'],
                y=fin_summary['Expenditure'],
                name='Expenditure',
                marker_color=INFO,
                hovertemplate="<b>%{x}</b><br>"
                              "Expenditure: KES %{y:,.0f}<extra></extra>",
            ))
            fig_fin.update_layout(
                barmode='group',
                legend=dict(
                    orientation='h', yanchor='bottom', y=1.02,
                    xanchor='right', x=1,
                    font=dict(size=11),
                ),
                showlegend=True,
            )
            _style_plotly(fig_fin, height=340)
            st.plotly_chart(fig_fin, use_container_width=True,
                            config={"displayModeBar": False})

    st.markdown("---")

    # =====================================================
    # WARD HEATMAP
    # =====================================================
    with st.container(border=True):
        st.markdown("##### 🗺️ Ward-Level Activity")
        ward_summary = (
            filtered.groupby(['subcounty', 'ward'])
            .agg(
                Projects=('id', 'count'),
                Funding=('total_funding', 'sum'),
                AvgProgress=('percentage_completion', 'mean'),
            )
            .reset_index()
        )
        fig_ward = px.treemap(
            ward_summary,
            path=[px.Constant("Embu County"), 'subcounty', 'ward'],
            values='Projects',
            color='AvgProgress',
            color_continuous_scale=[
                [0, "#fee2e2"], [0.5, "#fef3c7"], [1, "#d1fae5"]
            ],
            hover_data={'Funding': ':,.0f', 'AvgProgress': ':.1f'},
        )
        fig_ward.update_traces(
            textinfo="label+value",
            marker=dict(line=dict(color='white', width=2)),
            hovertemplate="<b>%{label}</b><br>"
                          "Projects: %{value}<br>"
                          "Funding: KES %{customdata[0]}<br>"
                          "Avg Progress: %{customdata[1]:.1f}%"
                          "<extra></extra>",
        )
        fig_ward.update_layout(
            height=380,
            margin=dict(l=10, r=10, t=20, b=10),
            coloraxis_colorbar=dict(
                title="Avg %",
                thickness=12,
                len=0.7,
                ticksuffix="%",
            ),
        )
        st.plotly_chart(fig_ward, use_container_width=True,
                        config={"displayModeBar": False})
        st.caption(
            "Box size = number of projects · Color = average completion % "
            "(green = higher, red = lower)"
        )

    st.markdown("---")

    # =====================================================
    # TOP PROJECTS + ATTENTION LIST
    # =====================================================
    att1, att2 = st.columns(2)

    # ---- Top funded ----
    with att1:
        with st.container(border=True):
            st.markdown("##### 💎 Top 5 Funded Projects")
            top_funded = (
                filtered.nlargest(5, 'total_funding')[
                    ['project_name', 'subcounty', 'total_funding',
                     'percentage_completion']
                ].reset_index(drop=True)
            )
            for _, row in top_funded.iterrows():
                pct = float(row['percentage_completion'] or 0)
                st.markdown(f"""
                    <div style="padding:12px 0;
                                border-bottom:1px solid #f1f5f9;">
                        <div style="font-size:13px; font-weight:600;
                                    color:#0f172a; margin-bottom:4px;">
                            {row['project_name'][:60]}{'...' if len(row['project_name']) > 60 else ''}
                        </div>
                        <div style="display:flex; justify-content:space-between;
                                    font-size:11px; color:#64748b;">
                            <span>📍 {row['subcounty']}</span>
                            <span style="color:{PRIMARY_DARK};
                                         font-weight:600;">
                                {_fmt_kes(row['total_funding'])}
                            </span>
                        </div>
                        <div style="background:#f1f5f9; border-radius:4px;
                                    height:4px; margin-top:6px;
                                    overflow:hidden;">
                            <div style="background:{SUCCESS};
                                        width:{pct}%; height:100%;"></div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

    # ---- Needs attention ----
    with att2:
        with st.container(border=True):
            st.markdown("##### ⚠️ Needs Attention")
            attention = filtered[
                filtered['project_status'].isin(['Stalled', 'Cancelled'])
                | (filtered['percentage_completion'] < 50)
            ].head(5)

            if attention.empty:
                st.success("✅ All projects are on track.")
            else:
                for _, row in attention.iterrows():
                    badge = _status_badge(row['project_status'])
                    pct = float(row['percentage_completion'] or 0)
                    st.markdown(f"""
                        <div style="padding:12px 0;
                                    border-bottom:1px solid #f1f5f9;">
                            <div style="display:flex;
                                        justify-content:space-between;
                                        align-items:flex-start;
                                        gap:8px; margin-bottom:4px;">
                                <div style="font-size:13px; font-weight:600;
                                            color:#0f172a;">
                                    {row['project_name'][:50]}{'...' if len(row['project_name']) > 50 else ''}
                                </div>
                                {badge}
                            </div>
                            <div style="font-size:11px; color:#64748b;">
                                📍 {row['subcounty']} · {row['ward']}
                                · Progress: <b>{pct:.1f}%</b>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

    st.markdown("---")

    # =====================================================
    # RECENT PROJECTS TABLE
    # =====================================================
    with st.container(border=True):
        st.markdown("##### 🕒 Recent Projects")

        recent = filtered.head(10)[
            ['project_name', 'subcounty', 'ward', 'department',
             'total_funding', 'total_expenditure',
             'percentage_completion', 'project_status']
        ].rename(columns={
            'project_name': 'Project Name',
            'subcounty': 'Subcounty',
            'ward': 'Ward',
            'department': 'Department',
            'total_funding': 'Funding (KES)',
            'total_expenditure': 'Expenditure (KES)',
            'percentage_completion': '% Complete',
            'project_status': 'Status',
        })

        st.dataframe(
            recent,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Project Name": st.column_config.TextColumn(
                    "Project Name", width="large"
                ),
                "Funding (KES)": st.column_config.NumberColumn(
                    format="KES %,.0f"
                ),
                "Expenditure (KES)": st.column_config.NumberColumn(
                    format="KES %,.0f"
                ),
                "% Complete": st.column_config.ProgressColumn(
                    "% Complete", format="%.1f%%",
                    min_value=0, max_value=100,
                ),
            },
        )

    # =====================================================
    # FOOTER
    # =====================================================
    st.markdown("---")
    st.markdown(f"""
        <div style="text-align:center; padding:16px; color:#94a3b8;
                    font-size:11px;">
            © Embu County Government · Project Management System · "
            "Land of Opportunities
        </div>
    """, unsafe_allow_html=True)
