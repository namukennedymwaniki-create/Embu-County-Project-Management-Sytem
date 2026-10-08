import streamlit as st
from utils.db import run_query, execute_write

st.title("⚙️ Settings")

tab1, tab2, tab3 = st.tabs(["Subcounties", "Wards", "Departments"])

with tab1:
    st.subheader("Manage Subcounties")
    sc_df = run_query("SELECT id, name, code FROM subcounties ORDER BY name")
    st.dataframe(sc_df, use_container_width=True)
    
    with st.form("add_subcounty"):
        name = st.text_input("Subcounty Name")
        code = st.text_input("Code (optional)")
        if st.form_submit_button("Add Subcounty"):
            success, msg = execute_write(
                "INSERT INTO subcounties (name, code) VALUES (:name, :code)",
                {"name": name, "code": code}
            )
            st.success(msg) if success else st.error(msg)

with tab2:
    st.subheader("Manage Wards")
    wards_df = run_query("""
        SELECT w.id, w.name, s.name as subcounty
        FROM wards w JOIN subcounties s ON w.subcounty_id = s.id
        ORDER BY s.name, w.name
    """)
    st.dataframe(wards_df, use_container_width=True)

with tab3:
    st.subheader("Manage Departments")
    dept_df = run_query("SELECT id, name, description FROM departments ORDER BY name")
    st.dataframe(dept_df, use_container_width=True)
