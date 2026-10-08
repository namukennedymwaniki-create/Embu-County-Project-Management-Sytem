"""
Projects view — Embu County Project Management System.
Professional filter bar, subcounty filtering, and detailed project views.
"""

import streamlit as st
import pandas as pd
from datetime import date, datetime
from utils.db import run_query, execute_write


# =====================================================
# HELPERS
# =====================================================
def _to_date(val):
    """Safely coerce a DB value to a Python date."""
    if val is None:
        return None
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    if isinstance(val, datetime):
        return val.date()
    try:
        return datetime.fromisoformat(str(val)[:10]).date()
    except Exception:
        return None


def _fmt_kes(value):
    """Format a number as Kenyan Shillings."""
    if value is None or pd.isna(value):
        return "KES 0"
    return f"KES {float(value):,.0f}"


def _status_badge(status):
    """Return a colored HTML badge for a status."""
    colors = {
        "Completed":    ("#065f46", "#d1fae5"),
        "In Progress":  ("#1e40af", "#dbeafe"),
        "Not Started":  ("#374151", "#e5e7eb"),
        "Stalled":      ("#92400e", "#fef3c7"),
        "Cancelled":    ("#991b1b", "#fee2e2"),
    }
    fg, bg = colors.get(status, ("#374151", "#e5e7eb"))
    return (
        f'<span style="background:{bg}; color:{fg}; padding:4px 12px; '
        f'border-radius:12px; font-size:12px; font-weight:600;">'
        f'{status}</span>'
    )


# =====================================================
# MAIN RENDER
# =====================================================
def render():
    st.title("📋 Project Management")
    st.caption("Embu County Government — Land of Opportunities")
    st.markdown("---")

    # =====================================================
    # LOAD REFERENCE DATA
    # =====================================================
    try:
        subcounties = run_query("SELECT id, name FROM subcounties ORDER BY name")
        wards = run_query("SELECT id, name, subcounty_id FROM wards ORDER BY name")
        departments = run_query("SELECT id, name FROM departments ORDER BY name")
    except Exception as e:
        st.error(f"⚠️ Could not load reference data: {e}")
        return

    # =====================================================
    # TABS: View Projects / Add New Project
    # =====================================================
    tab_view, tab_add = st.tabs(["📊 View Projects", "➕ Add New Project"])

    # =====================================================
    # TAB 1 — VIEW PROJECTS (filter bar + table + details)
    # =====================================================
    with tab_view:
        _render_projects_view(subcounties, wards, departments)

    # =====================================================
    # TAB 2 — ADD NEW PROJECT
    # =====================================================
    with tab_add:
        _render_add_project(subcounties, wards, departments)


# =====================================================
# TAB 1: VIEW PROJECTS
# =====================================================
def _render_projects_view(subcounties, wards, departments):
    # ---- Load all projects ----
    try:
        projects_df = run_query("""
            SELECT
                p.id,
                p.project_name,
                s.name AS subcounty,
                w.name AS ward,
                d.name AS department,
                p.commencement_date,
                p.expected_completion_date,
                p.total_funding,
                p.total_expenditure,
                p.percentage_completion,
                p.project_status,
                p.remarks
            FROM projects p
            LEFT JOIN subcounties s ON p.subcounty_id = s.id
            LEFT JOIN wards w ON p.ward_id = w.id
            LEFT JOIN departments d ON p.department_id = d.id
            ORDER BY p.id DESC
        """)
    except Exception as e:
        st.error(f"⚠️ Could not load projects: {e}")
        return

    if projects_df.empty:
        st.info("No projects yet. Use the **Add New Project** tab to create one.")
        return

    # =====================================================
    # PROFESSIONAL FILTER BAR
    # =====================================================
    st.markdown("### 🔎 Filter Projects")

    with st.container(border=True):
        row1_col1, row1_col2, row1_col3 = st.columns(3)

        # ---- Subcounty (primary filter) ----
        subcounty_options = ["All Subcounties"] + sorted(
            projects_df['subcounty'].dropna().unique().tolist()
        )
        selected_subcounty = row1_col1.selectbox(
            "📍 Subcounty",
            options=subcounty_options,
            index=0,
            key="proj_filter_subcounty",
        )

        # ---- Ward (cascades from subcounty) ----
        if selected_subcounty == "All Subcounties":
            ward_source = projects_df['ward'].dropna().unique().tolist()
        else:
            ward_source = projects_df[
                projects_df['subcounty'] == selected_subcounty
            ]['ward'].dropna().unique().tolist()
        ward_options = ["All Wards"] + sorted(ward_source)
        selected_ward = row1_col2.selectbox(
            "🗺️ Ward",
            options=ward_options,
            index=0,
            key="proj_filter_ward",
        )

        # ---- Department ----
        dept_options = ["All Departments"] + sorted(
            projects_df['department'].dropna().unique().tolist()
        )
        selected_dept = row1_col3.selectbox(
            "🏢 Department",
            options=dept_options,
            index=0,
            key="proj_filter_dept",
        )

        row2_col1, row2_col2, row2_col3 = st.columns(3)

        # ---- Status ----
        status_options = ["All Statuses"] + [
            "Completed", "In Progress", "Not Started", "Stalled", "Cancelled"
        ]
        selected_status = row2_col1.selectbox(
            "📊 Project Status",
            options=status_options,
            index=0,
            key="proj_filter_status",
        )

        # ---- Search ----
        search_term = row2_col2.text_input(
            "🔍 Search Project Name",
            placeholder="Type to search...",
            key="proj_filter_search",
        )

        # ---- Reset ----
        row2_col3.markdown("<br>", unsafe_allow_html=True)
        if row2_col3.button(
            "🔄 Reset Filters",
            use_container_width=True,
            key="proj_filter_reset",
        ):
            for k in [
                "proj_filter_subcounty",
                "proj_filter_ward",
                "proj_filter_dept",
                "proj_filter_status",
                "proj_filter_search",
            ]:
                st.session_state.pop(k, None)
            st.rerun()

    # =====================================================
    # APPLY FILTERS
    # =====================================================
    view_df = projects_df.copy()
    if selected_subcounty != "All Subcounties":
        view_df = view_df[view_df['subcounty'] == selected_subcounty]
    if selected_ward != "All Wards":
        view_df = view_df[view_df['ward'] == selected_ward]
    if selected_dept != "All Departments":
        view_df = view_df[view_df['department'] == selected_dept]
    if selected_status != "All Statuses":
        view_df = view_df[view_df['project_status'] == selected_status]
    if search_term.strip():
        view_df = view_df[
            view_df['project_name'].str.contains(
                search_term.strip(), case=False, na=False
            )
        ]

    # =====================================================
    # SUMMARY METRICS
    # =====================================================
    st.markdown("### 📈 Summary")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Projects", f"{len(view_df):,}")
    m2.metric(
        "Total Funding",
        _fmt_kes(view_df['total_funding'].sum() if not view_df.empty else 0),
    )
    m3.metric(
        "Total Expenditure",
        _fmt_kes(view_df['total_expenditure'].sum() if not view_df.empty else 0),
    )
    avg_pct = (
        view_df['percentage_completion'].mean() if not view_df.empty else 0
    )
    m4.metric("Avg. Completion", f"{avg_pct:.1f}%")

    st.markdown("---")

    # =====================================================
    # PROJECTS TABLE
    # =====================================================
    st.markdown(f"### 📑 Projects ({len(view_df)})")

    if view_df.empty:
        st.warning("No projects match the current filters.")
        return

    # Build display table
    display_df = view_df.copy()
    display_df.insert(0, 'S/No', range(1, len(display_df) + 1))

    display_df = display_df.rename(columns={
        'project_name': 'Project Name',
        'ward': 'Ward',
        'subcounty': 'Subcounty',
        'commencement_date': 'Commencement',
        'expected_completion_date': 'Expected Completion',
        'department': 'Department',
        'total_funding': 'Total Funding (KES)',
        'total_expenditure': 'Total Expenditure (KES)',
        'percentage_completion': '% Completion',
        'remarks': 'Remarks',
    })

    table_cols = [
        'S/No', 'Project Name', 'Ward', 'Subcounty',
        'Commencement', 'Expected Completion', 'Department',
        'Total Funding (KES)', 'Total Expenditure (KES)',
        '% Completion', 'Remarks',
    ]
    display_df = display_df[table_cols]

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=420,
        column_config={
            "S/No": st.column_config.NumberColumn("S/No", width="small"),
            "Project Name": st.column_config.TextColumn(
                "Project Name", width="large"
            ),
            "Ward": st.column_config.TextColumn("Ward", width="small"),
            "Subcounty": st.column_config.TextColumn("Subcounty", width="small"),
            "Commencement": st.column_config.DateColumn(
                "Commencement", format="DD MMM YYYY", width="small"
            ),
            "Expected Completion": st.column_config.DateColumn(
                "Expected Completion", format="DD MMM YYYY", width="small"
            ),
            "Department": st.column_config.TextColumn(
                "Department", width="medium"
            ),
            "Total Funding (KES)": st.column_config.NumberColumn(
                "Total Funding (KES)", format="KES %,.0f"
            ),
            "Total Expenditure (KES)": st.column_config.NumberColumn(
                "Total Expenditure (KES)", format="KES %,.0f"
            ),
            "% Completion": st.column_config.ProgressColumn(
                "% Completion",
                format="%.1f%%",
                min_value=0,
                max_value=100,
            ),
            "Remarks": st.column_config.TextColumn(
                "Remarks", width="medium"
            ),
        },
    )

    # =====================================================
    # PROJECT DETAILS VIEWER
    # =====================================================
    st.markdown("---")
    st.markdown("### 🔍 Project Details")

    # Select a project to inspect
    detail_options = view_df.copy()
    detail_options['label'] = (
        "#" + detail_options['id'].astype(str) + " — "
        + detail_options['project_name']
    )

    selected_label = st.selectbox(
        "Select a project to view full details",
        options=detail_options['label'].tolist(),
        key="proj_detail_select",
        label_visibility="collapsed",
    )

    selected_id = int(selected_label.split(" — ")[0].replace("#", ""))
    proj = view_df[view_df['id'] == selected_id].iloc[0]

    # ---- Detail card ----
    with st.container(border=True):
        # Header
        h1, h2 = st.columns([3, 1])
        h1.markdown(f"#### {proj['project_name']}")
        h2.markdown(
            f"<div style='text-align:right;'>{_status_badge(proj['project_status'])}</div>",
            unsafe_allow_html=True,
        )

        st.markdown("---")

        # Row 1: Location
        r1c1, r1c2, r1c3 = st.columns(3)
        r1c1.markdown(
            f"**📍 Subcounty**  \n{proj['subcounty'] or '—'}"
        )
        r1c2.markdown(
            f"**🗺️ Ward**  \n{proj['ward'] or '—'}"
        )
        r1c3.markdown(
            f"**🏢 Department**  \n{proj['department'] or '—'}"
        )

        st.markdown("")

        # Row 2: Timeline
        r2c1, r2c2, r2c3 = st.columns(3)
        comm = _to_date(proj['commencement_date'])
        exp = _to_date(proj['expected_completion_date'])
        r2c1.markdown(
            f"**📅 Commencement Date**  \n"
            f"{comm.strftime('%d %b %Y') if comm else '—'}"
        )
        r2c2.markdown(
            f"**🎯 Expected Completion**  \n"
            f"{exp.strftime('%d %b %Y') if exp else '—'}"
        )
        r2c3.markdown(
            f"**⏱️ Duration**  \n"
            f"{(exp - comm).days if comm and exp else '—'}"
            f"{' days' if comm and exp else ''}"
        )

        st.markdown("")

        # Row 3: Financials
        r3c1, r3c2, r3c3 = st.columns(3)
        funding = proj['total_funding'] or 0
        expenditure = proj['total_expenditure'] or 0
        balance = funding - expenditure
        r3c1.markdown(
            f"**💰 Total Funding**  \n{_fmt_kes(funding)}"
        )
        r3c2.markdown(
            f"**💸 Total Expenditure**  \n{_fmt_kes(expenditure)}"
        )
        r3c3.markdown(
            f"**🏦 Balance Remaining**  \n{_fmt_kes(balance)}"
        )

        st.markdown("")

        # Row 4: Progress bar
        pct = float(proj['percentage_completion'] or 0)
        st.markdown(f"**📊 Completion Progress — {pct:.1f}%**")
        st.progress(min(max(pct / 100.0, 0.0), 1.0))

        st.markdown("")

        # Row 5: Remarks
        st.markdown(
            f"**📝 Remarks**  \n{proj['remarks'] or '_No remarks recorded._'}"
        )

    # =====================================================
    # EXPORT
    # =====================================================
    st.markdown("---")
    csv = display_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        "⬇️ Download Filtered Projects (CSV)",
        data=csv,
        file_name=f"embu_projects_{date.today().isoformat()}.csv",
        mime="text/csv",
        use_container_width=False,
    )

    # =====================================================
    # EDIT / DELETE IN EXPANDERS
    # =====================================================
    st.markdown("---")

    with st.expander("✏️ Update Project"):
        _render_edit_form(projects_df, subcounties, wards, departments)

    with st.expander("🗑️ Delete Project"):
        _render_delete_form(projects_df)


# =====================================================
# TAB 2: ADD NEW PROJECT
# =====================================================
def _render_add_project(subcounties, wards, departments):
    if subcounties.empty or departments.empty:
        st.warning(
            "⚠️ Please add Subcounties and Departments in the **Settings** "
            "module before creating projects."
        )
        return

    with st.form("new_project", clear_on_submit=True):
        st.markdown("**Basic Details**")
        col1, col2 = st.columns(2)

        project_name = col1.text_input("Project Name *")

        subcounty_id = col2.selectbox(
            "Subcounty *",
            options=subcounties['id'].tolist(),
            format_func=lambda x: subcounties.loc[
                subcounties['id'] == x, 'name'
            ].values[0],
        )

        filtered_wards = wards[wards['subcounty_id'] == subcounty_id]
        if not filtered_wards.empty:
            ward_id = col1.selectbox(
                "Ward *",
                options=filtered_wards['id'].tolist(),
                format_func=lambda x: filtered_wards.loc[
                    filtered_wards['id'] == x, 'name'
                ].values[0],
            )
        else:
            col1.warning("No wards found for this subcounty.")
            ward_id = None

        department_id = col2.selectbox(
            "Department *",
            options=departments['id'].tolist(),
            format_func=lambda x: departments.loc[
                departments['id'] == x, 'name'
            ].values[0],
        )

        st.markdown("**Timeline**")
        col3, col4 = st.columns(2)
        commencement_date = col3.date_input(
            "Project Commencement Date", value=None
        )
        expected_completion_date = col4.date_input(
            "Expected Date of Completion", value=None
        )

        st.markdown("**Financials (KES)**")
        col5, col6 = st.columns(2)
        total_funding = col5.number_input(
            "Total Funding", min_value=0.0, step=1000.0, format="%.2f"
        )
        total_expenditure = col6.number_input(
            "Total Expenditure", min_value=0.0, step=1000.0, format="%.2f"
        )

        st.markdown("**Progress**")
        col7, col8 = st.columns(2)
        percentage_completion = col7.slider(
            "Percentage (%) of Completion",
            min_value=0, max_value=100, value=0, step=1,
        )
        project_status = col8.selectbox(
            "Status",
            ["Not Started", "In Progress", "Completed", "Stalled", "Cancelled"],
        )

        remarks = st.text_area("Remarks")

        submitted = st.form_submit_button(
            "💾 Save Project", use_container_width=True
        )

        if submitted:
            if not project_name.strip() or not ward_id:
                st.error("Project Name and Ward are required.")
            elif total_expenditure > total_funding and total_funding > 0:
                st.error("Total Expenditure cannot exceed Total Funding.")
            elif (
                commencement_date and expected_completion_date
                and expected_completion_date < commencement_date
            ):
                st.error(
                    "Expected Completion Date cannot be before Commencement Date."
                )
            else:
                ok, msg = execute_write(
                    """
                    INSERT INTO projects
                        (project_name, subcounty_id, ward_id,
                         department_id, project_status, remarks,
                         commencement_date, expected_completion_date,
                         total_funding, total_expenditure,
                         percentage_completion)
                    VALUES
                        (:name, :sc, :ward, :dept, :status, :remarks,
                         :comm, :exp, :fund, :spent, :pct)
                    """,
                    {
                        "name": project_name.strip(),
                        "sc": subcounty_id,
                        "ward": ward_id,
                        "dept": department_id,
                        "status": project_status,
                        "remarks": remarks.strip() or None,
                        "comm": commencement_date,
                        "exp": expected_completion_date,
                        "fund": total_funding,
                        "spent": total_expenditure,
                        "pct": float(percentage_completion),
                    },
                )
                if ok:
                    st.success("✅ Project saved successfully.")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")


# =====================================================
# UPDATE PROJECT
# =====================================================
def _render_edit_form(projects_df, subcounties, wards, departments):
    edit_id = st.selectbox(
        "Select project to edit",
        options=projects_df['id'].tolist(),
        format_func=lambda x: f"#{x} — "
        f"{projects_df.loc[projects_df['id'] == x, 'project_name'].values[0]}",
        key="edit_project_select",
    )

    current = projects_df[projects_df['id'] == edit_id].iloc[0]

    with st.form("edit_project"):
        st.markdown("**Basic Details**")
        col1, col2 = st.columns(2)
        new_name = col1.text_input("Project Name", value=current['project_name'])

        sc_ids = subcounties['id'].tolist()
        sc_names = subcounties['name'].tolist()
        current_sc_name = current['subcounty']
        sc_index = sc_names.index(current_sc_name) if current_sc_name in sc_names else 0
        new_sc_id = col2.selectbox(
            "Subcounty", options=sc_ids, index=sc_index,
            format_func=lambda x: subcounties.loc[
                subcounties['id'] == x, 'name'
            ].values[0],
            key="edit_sc",
        )

        ward_subset = wards[wards['subcounty_id'] == new_sc_id]
        ward_ids = ward_subset['id'].tolist()
        ward_names = ward_subset['name'].tolist()
        current_ward_name = current['ward']
        ward_index = ward_names.index(current_ward_name) \
            if current_ward_name in ward_names else 0
        new_ward_id = col1.selectbox(
            "Ward", options=ward_ids, index=ward_index,
            format_func=lambda x: ward_subset.loc[
                ward_subset['id'] == x, 'name'
            ].values[0],
            key="edit_ward",
        ) if ward_ids else None

        dept_ids = departments['id'].tolist()
        dept_names = departments['name'].tolist()
        current_dept_name = current['department']
        dept_index = dept_names.index(current_dept_name) \
            if current_dept_name in dept_names else 0
        new_dept_id = col2.selectbox(
            "Department", options=dept_ids, index=dept_index,
            format_func=lambda x: departments.loc[
                departments['id'] == x, 'name'
            ].values[0],
            key="edit_dept",
        )

        st.markdown("**Timeline**")
        col3, col4 = st.columns(2)
        new_commencement = col3.date_input(
            "Project Commencement Date",
            value=_to_date(current['commencement_date']),
        )
        new_expected = col4.date_input(
            "Expected Date of Completion",
            value=_to_date(current['expected_completion_date']),
        )

        st.markdown("**Financials (KES)**")
        col5, col6 = st.columns(2)
        new_funding = col5.number_input(
            "Total Funding", min_value=0.0, step=1000.0,
            value=float(current['total_funding'] or 0), format="%.2f",
        )
        new_expenditure = col6.number_input(
            "Total Expenditure", min_value=0.0, step=1000.0,
            value=float(current['total_expenditure'] or 0), format="%.2f",
        )

        st.markdown("**Progress**")
        col7, col8 = st.columns(2)
        new_pct = col7.slider(
            "Percentage (%) of Completion",
            min_value=0, max_value=100,
            value=int(current['percentage_completion'] or 0), step=1,
        )
        statuses = ["Not Started", "In Progress", "Completed", "Stalled", "Cancelled"]
        status_index = statuses.index(current['project_status']) \
            if current['project_status'] in statuses else 0
        new_status = col8.selectbox(
            "Status", statuses, index=status_index, key="edit_status"
        )

        new_remarks = st.text_area(
            "Remarks", value=current['remarks'] or "", key="edit_remarks"
        )

        if st.form_submit_button("💾 Update Project", use_container_width=True):
            if not new_name.strip() or not new_ward_id:
                st.error("Project Name and Ward are required.")
            elif new_expenditure > new_funding and new_funding > 0:
                st.error("Total Expenditure cannot exceed Total Funding.")
            elif (
                new_commencement and new_expected
                and new_expected < new_commencement
            ):
                st.error(
                    "Expected Completion Date cannot be before Commencement Date."
                )
            else:
                ok, msg = execute_write(
                    """
                    UPDATE projects
                    SET project_name = :name,
                        subcounty_id = :sc,
                        ward_id = :ward,
                        department_id = :dept,
                        project_status = :status,
                        remarks = :remarks,
                        commencement_date = :comm,
                        expected_completion_date = :exp,
                        total_funding = :fund,
                        total_expenditure = :spent,
                        percentage_completion = :pct,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = :id
                    """,
                    {
                        "name": new_name.strip(),
                        "sc": new_sc_id,
                        "ward": new_ward_id,
                        "dept": new_dept_id,
                        "status": new_status,
                        "remarks": new_remarks.strip() or None,
                        "comm": new_commencement,
                        "exp": new_expected,
                        "fund": new_funding,
                        "spent": new_expenditure,
                        "pct": float(new_pct),
                        "id": edit_id,
                    },
                )
                if ok:
                    st.success(f"✅ Project #{edit_id} updated.")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")


# =====================================================
# DELETE PROJECT
# =====================================================
def _render_delete_form(projects_df):
    del_id = st.selectbox(
        "Select project to delete",
        options=projects_df['id'].tolist(),
        format_func=lambda x: f"#{x} — "
        f"{projects_df.loc[projects_df['id'] == x, 'project_name'].values[0]}",
        key="delete_project_select",
    )

    confirm = st.checkbox(
        f"I confirm I want to permanently delete project #{del_id}",
        key="delete_confirm",
    )

    if st.button(
        "Delete Project", type="primary",
        disabled=not confirm, use_container_width=True,
    ):
        ok, msg = execute_write(
            "DELETE FROM projects WHERE id = :id", {"id": del_id}
        )
        if ok:
            st.success(f"✅ Project #{del_id} deleted.")
            st.cache_data.clear()
            st.rerun()
        else:
            st.error(f"❌ {msg}")
