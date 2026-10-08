import streamlit as st
from utils.db import run_query, execute_write

st.title("📋 Project Management")

# Load reference data
subcounties = run_query("SELECT id, name FROM subcounties ORDER BY name")
wards = run_query("SELECT id, name, subcounty_id FROM wards ORDER BY name")
departments = run_query("SELECT id, name FROM departments ORDER BY name")

# Create form
with st.expander("➕ Add New Project", expanded=False):
    with st.form("new_project"):
        col1, col2 = st.columns(2)
        project_name = col1.text_input("Project Name")
        subcounty_id = col2.selectbox("Subcounty", subcounties['id'],
                                       format_func=lambda x: subcounties[subcounties['id']==x]['name'].values[0])
        
        # Filter wards by selected subcounty
        filtered_wards = wards[wards['subcounty_id'] == subcounty_id] if subcounty_id else wards
        ward_id = st.selectbox("Ward", filtered_wards['id'],
                               format_func=lambda x: filtered_wards[filtered_wards['id']==x]['name'].values[0])
        
        contract_sum = col1.number_input("Contract Sum (KES)", min_value=0.0, step=1000.0)
        department_id = col2.selectbox("Department", departments['id'],
                                       format_func=lambda x: departments[departments['id']==x]['name'].values[0])
        project_status = st.selectbox("Status", 
            ["Not Started", "In Progress", "Completed", "Stalled", "Cancelled"])
        remarks = st.text_area("Remarks")
        
        if st.form_submit_button("Save Project"):
            success, msg = execute_write("""
                INSERT INTO projects (project_name, subcounty_id, ward_id, contract_sum, 
                                      department_id, project_status, remarks)
                VALUES (:name, :sc, :ward, :sum, :dept, :status, :remarks)
            """, {
                "name": project_name, "sc": subcounty_id, "ward": ward_id,
                "sum": contract_sum, "dept": department_id, 
                "status": project_status, "remarks": remarks
            })
            st.success(msg) if success else st.error(msg)

# Display existing projects with edit/delete
st.subheader("Existing Projects")
projects_df = run_query("""
    SELECT p.id, p.project_name, s.name as subcounty, w.name as ward,
           p.contract_sum, d.name as department, p.project_status, p.remarks
    FROM projects p
    LEFT JOIN subcounties s ON p.subcounty_id = s.id
    LEFT JOIN wards w ON p.ward_id = w.id
    LEFT JOIN departments d ON p.department_id = d.id
    ORDER BY p.id DESC
""")

# Use st.data_editor for inline editing
edited = st.data_editor(projects_df, use_container_width=True, 
                        disabled=["id"], hide_index=True)
