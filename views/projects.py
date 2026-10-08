"""Projects — CRUD module for Embu County PMS."""

import streamlit as st
from utils.db import run_query, execute_write

def render():
    st.title("📋 Project Management")

st.title("📋 Project Management")
st.caption("Add, edit, and manage county projects")
st.markdown("---")

# Load reference data
subcounties = run_query("SELECT id, name FROM subcounties ORDER BY name")
wards = run_query("SELECT id, name, subcounty_id FROM wards ORDER BY name")
departments = run_query("SELECT id, name FROM departments ORDER BY name")

# =====================================================
# ADD NEW PROJECT
# =====================================================
with st.expander("➕ Add New Project", expanded=False):
    with st.form("new_project", clear_on_submit=True):
        col1, col2 = st.columns(2)

        project_name = col1.text_input("Project Name *")

        if not subcounties.empty:
            subcounty_id = col2.selectbox(
                "Subcounty *",
                options=subcounties['id'].tolist(),
                format_func=lambda x: subcounties.loc[
                    subcounties['id'] == x, 'name'
                ].values[0],
            )
        else:
            st.warning("No subcounties found. Add them in Settings first.")
            subcounty_id = None

        filtered_wards = wards[wards['subcounty_id'] == subcounty_id] \
            if subcounty_id else wards
        if not filtered_wards.empty:
            ward_id = col1.selectbox(
                "Ward *",
                options=filtered_wards['id'].tolist(),
                format_func=lambda x: filtered_wards.loc[
                    filtered_wards['id'] == x, 'name'
                ].values[0],
            )
        else:
            col1.warning("No wards for selected subcounty.")
            ward_id = None

        contract_sum = col1.number_input(
            "Contract Sum (KES) *", min_value=0.0, step=1000.0, format="%.2f"
        )

        if not departments.empty:
            department_id = col2.selectbox(
                "Department *",
                options=departments['id'].tolist(),
                format_func=lambda x: departments.loc[
                    departments['id'] == x, 'name'
                ].values[0],
            )
        else:
            department_id = None

        project_status = col2.selectbox(
            "Status *",
            ["Not Started", "In Progress", "Completed", "Stalled", "Cancelled"],
        )

        remarks = st.text_area("Remarks")

        if st.form_submit_button("💾 Save Project", use_container_width=True):
            if not project_name or not subcounty_id or not ward_id or not department_id:
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
                        "name": project_name,
                        "sc": subcounty_id,
                        "ward": ward_id,
                        "sum": contract_sum,
                        "dept": department_id,
                        "status": project_status,
                        "remarks": remarks,
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

if projects_df.empty:
    st.info("No projects yet. Add one above.")
else:
    st.dataframe(
        projects_df,
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

    # Delete section
    with st.expander("🗑️ Delete a Project"):
        delete_id = st.selectbox(
            "Select project ID to delete",
            options=projects_df['id'].tolist(),
            format_func=lambda x: f"#{x} — "
            f"{projects_df.loc[projects_df['id'] == x, 'project_name'].values[0]}",
        )
        if st.button("Delete Project", type="primary"):
            ok, msg = execute_write(
                "DELETE FROM projects WHERE id = :id", {"id": delete_id}
            )
            if ok:
                st.success(f"Project #{delete_id} deleted.")
                st.cache_data.clear()
                st.rerun()
            else:
                st.error(msg)
