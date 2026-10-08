"""
Projects view — Embu County Project Management System.
CRUD module for county projects.
"""

import streamlit as st
from utils.db import run_query, execute_write


def render():
    st.title("📋 Project Management")
    st.caption("Add, edit, and manage county projects")
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
    # ADD NEW PROJECT
    # =====================================================
    with st.expander("➕ Add New Project", expanded=False):
        if subcounties.empty or departments.empty:
            st.warning(
                "⚠️ Please add Subcounties and Departments in the **Settings** "
                "module before creating projects."
            )
        else:
            with st.form("new_project", clear_on_submit=True):
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

                contract_sum = col1.number_input(
                    "Contract Sum (KES) *",
                    min_value=0.0,
                    step=1000.0,
                    format="%.2f",
                )

                department_id = col2.selectbox(
                    "Department *",
                    options=departments['id'].tolist(),
                    format_func=lambda x: departments.loc[
                        departments['id'] == x, 'name'
                    ].values[0],
                )

                project_status = col2.selectbox(
                    "Status *",
                    ["Not Started", "In Progress", "Completed", "Stalled", "Cancelled"],
                )

                remarks = st.text_area("Remarks")

                submitted = st.form_submit_button(
                    "💾 Save Project", use_container_width=True
                )

                if submitted:
                    if not project_name.strip() or not ward_id:
                        st.error("Please fill in all required fields.")
                    else:
                        ok, msg = execute_write(
                            """
                            INSERT INTO projects
                                (project_name, subcounty_id, ward_id, contract_sum,
                                 department_id, project_status, remarks)
                            VALUES
                                (:name, :sc, :ward, :sum, :dept, :status, :remarks)
                            """,
                            {
                                "name": project_name.strip(),
                                "sc": subcounty_id,
                                "ward": ward_id,
                                "sum": contract_sum,
                                "dept": department_id,
                                "status": project_status,
                                "remarks": remarks.strip() or None,
                            },
                        )
                        if ok:
                            st.success("✅ Project saved successfully.")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")

    st.markdown("---")

    # =====================================================
    # EXISTING PROJECTS
    # =====================================================
    st.subheader("📑 Existing Projects")

    try:
        projects_df = run_query("""
            SELECT
                p.id,
                p.project_name,
                s.name AS subcounty,
                w.name AS ward,
                p.contract_sum,
                d.name AS department,
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
        st.info("No projects yet. Add one above.")
        return

    # ----- FILTER BAR -----
    col_f1, col_f2, col_f3 = st.columns(3)
    f_subcounty = col_f1.multiselect(
        "Filter by Subcounty",
        options=sorted(projects_df['subcounty'].dropna().unique().tolist()),
        key="proj_filter_subcounty",
    )
    f_status = col_f2.multiselect(
        "Filter by Status",
        options=sorted(projects_df['project_status'].dropna().unique().tolist()),
        key="proj_filter_status",
    )
    f_dept = col_f3.multiselect(
        "Filter by Department",
        options=sorted(projects_df['department'].dropna().unique().tolist()),
        key="proj_filter_dept",
    )

    view_df = projects_df.copy()
    if f_subcounty:
        view_df = view_df[view_df['subcounty'].isin(f_subcounty)]
    if f_status:
        view_df = view_df[view_df['project_status'].isin(f_status)]
    if f_dept:
        view_df = view_df[view_df['department'].isin(f_dept)]

    st.dataframe(
        view_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "id": st.column_config.NumberColumn("ID", width="small"),
            "project_name": "Project Name",
            "subcounty": "Subcounty",
            "ward": "Ward",
            "contract_sum": st.column_config.NumberColumn(
                "Contract Sum (KES)", format="KES %,.0f"
            ),
            "department": "Department",
            "project_status": "Status",
            "remarks": "Remarks",
        },
    )

    st.caption(f"Showing {len(view_df)} of {len(projects_df)} projects")

    st.markdown("---")

    # =====================================================
    # UPDATE PROJECT
    # =====================================================
    st.subheader("✏️ Update Project")

    with st.expander("Edit an existing project", expanded=False):
        edit_id = st.selectbox(
            "Select project to edit",
            options=projects_df['id'].tolist(),
            format_func=lambda x: f"#{x} — "
            f"{projects_df.loc[projects_df['id'] == x, 'project_name'].values[0]}",
            key="edit_project_select",
        )

        current = projects_df[projects_df['id'] == edit_id].iloc[0]

        with st.form("edit_project"):
            col1, col2 = st.columns(2)

            new_name = col1.text_input("Project Name", value=current['project_name'])

            # Subcounty
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

            # Ward (filtered by subcounty)
            ward_subset = wards[wards['subcounty_id'] == new_sc_id]
            ward_ids = ward_subset['id'].tolist()
            ward_names = ward_subset['name'].tolist()
            current_ward_name = current['ward']
            ward_index = ward_names.index(current_ward_name) if current_ward_name in ward_names else 0
            new_ward_id = col1.selectbox(
                "Ward", options=ward_ids, index=ward_index,
                format_func=lambda x: ward_subset.loc[
                    ward_subset['id'] == x, 'name'
                ].values[0],
                key="edit_ward",
            ) if ward_ids else None

            new_sum = col1.number_input(
                "Contract Sum (KES)",
                min_value=0.0,
                step=1000.0,
                value=float(current['contract_sum'] or 0),
                format="%.2f",
            )

            dept_ids = departments['id'].tolist()
            dept_names = departments['name'].tolist()
            current_dept_name = current['department']
            dept_index = dept_names.index(current_dept_name) if current_dept_name in dept_names else 0
            new_dept_id = col2.selectbox(
                "Department", options=dept_ids, index=dept_index,
                format_func=lambda x: departments.loc[
                    departments['id'] == x, 'name'
                ].values[0],
                key="edit_dept",
            )

            statuses = ["Not Started", "In Progress", "Completed", "Stalled", "Cancelled"]
            status_index = statuses.index(current['project_status']) \
                if current['project_status'] in statuses else 0
            new_status = col2.selectbox(
                "Status", statuses, index=status_index, key="edit_status"
            )

            new_remarks = st.text_area(
                "Remarks", value=current['remarks'] or "", key="edit_remarks"
            )

            if st.form_submit_button("💾 Update Project", use_container_width=True):
                if not new_name.strip() or not new_ward_id:
                    st.error("Project name and ward are required.")
                else:
                    ok, msg = execute_write(
                        """
                        UPDATE projects
                        SET project_name = :name,
                            subcounty_id = :sc,
                            ward_id = :ward,
                            contract_sum = :sum,
                            department_id = :dept,
                            project_status = :status,
                            remarks = :remarks
                        WHERE id = :id
                        """,
                        {
                            "name": new_name.strip(),
                            "sc": new_sc_id,
                            "ward": new_ward_id,
                            "sum": new_sum,
                            "dept": new_dept_id,
                            "status": new_status,
                            "remarks": new_remarks.strip() or None,
                            "id": edit_id,
                        },
                    )
                    if ok:
                        st.success(f"✅ Project #{edit_id} updated.")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

    st.markdown("---")

    # =====================================================
    # DELETE PROJECT
    # =====================================================
    st.subheader("🗑️ Delete Project")

    with st.expander("Delete a project", expanded=False):
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
            disabled=not confirm,
            use_container_width=True,
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
