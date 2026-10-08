"""Settings — Manage subcounties, wards, departments."""

import streamlit as st
from utils.db import run_query, execute_write

def render():
    st.title("⚙️ Settings")
    
st.title("⚙️ Settings")
st.caption("Manage reference data for the county project system")
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["Subcounties", "Wards", "Departments"])

# ---------------- SUBCOUNTIES ----------------
with tab1:
    st.subheader("Manage Subcounties")
    sc_df = run_query("SELECT id, name, code FROM subcounties ORDER BY name")

    if sc_df.empty:
        st.info("No subcounties yet.")
    else:
        st.dataframe(sc_df, use_container_width=True, hide_index=True)

    with st.form("add_subcounty", clear_on_submit=True):
        name = st.text_input("Subcounty Name")
        code = st.text_input("Code (optional)")
        if st.form_submit_button("Add Subcounty"):
            if not name.strip():
                st.error("Name is required.")
            else:
                ok, msg = execute_write(
                    "INSERT INTO subcounties (name, code) VALUES (:name, :code)",
                    {"name": name.strip(), "code": code.strip() or None},
                )
                if ok:
                    st.success("Subcounty added.")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error(msg)

# ---------------- WARDS ----------------
with tab2:
    st.subheader("Manage Wards")
    wards_df = run_query("""
        SELECT w.id, w.name, s.name AS subcounty
        FROM wards w
        JOIN subcounties s ON w.subcounty_id = s.id
        ORDER BY s.name, w.name
    """)

    if wards_df.empty:
        st.info("No wards yet.")
    else:
        st.dataframe(wards_df, use_container_width=True, hide_index=True)

    sc_options = run_query("SELECT id, name FROM subcounties ORDER BY name")
    if not sc_options.empty:
        with st.form("add_ward", clear_on_submit=True):
            ward_name = st.text_input("Ward Name")
            sc_id = st.selectbox(
                "Subcounty",
                options=sc_options['id'].tolist(),
                format_func=lambda x: sc_options.loc[
                    sc_options['id'] == x, 'name'
                ].values[0],
            )
            if st.form_submit_button("Add Ward"):
                if not ward_name.strip():
                    st.error("Ward name is required.")
                else:
                    ok, msg = execute_write(
                        "INSERT INTO wards (name, subcounty_id) VALUES (:name, :sc)",
                        {"name": ward_name.strip(), "sc": sc_id},
                    )
                    if ok:
                        st.success("Ward added.")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(msg)
    else:
        st.warning("Add subcounties first before adding wards.")

# ---------------- DEPARTMENTS ----------------
with tab3:
    st.subheader("Manage Departments")
    dept_df = run_query("SELECT id, name, description FROM departments ORDER BY name")

    if dept_df.empty:
        st.info("No departments yet.")
    else:
        st.dataframe(dept_df, use_container_width=True, hide_index=True)

    with st.form("add_department", clear_on_submit=True):
        dept_name = st.text_input("Department Name")
        dept_desc = st.text_area("Description (optional)")
        if st.form_submit_button("Add Department"):
            if not dept_name.strip():
                st.error("Name is required.")
            else:
                ok, msg = execute_write(
                    """INSERT INTO departments (name, description)
                       VALUES (:name, :desc)""",
                    {"name": dept_name.strip(), "desc": dept_desc.strip() or None},
                )
                if ok:
                    st.success("Department added.")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error(msg)
