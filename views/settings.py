"""
Settings view — Embu County Project Management System.
Manage subcounties, wards, and departments.
"""

import streamlit as st
from utils.db import run_query, execute_write


def render():
    st.title("⚙️ Settings")
    st.caption("Manage reference data for the county project system")
    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["🏘️ Subcounties", "🗺️ Wards", "🏢 Departments"])

    # =====================================================
    # SUBCOUNTIES
    # =====================================================
    with tab1:
        st.subheader("Manage Subcounties")

        sc_df = run_query("SELECT id, name, code FROM subcounties ORDER BY name")

        if sc_df.empty:
            st.info("No subcounties yet. Add one below.")
        else:
            st.dataframe(sc_df, use_container_width=True, hide_index=True)

        st.markdown("**Add New Subcounty**")
        with st.form("add_subcounty", clear_on_submit=True):
            col1, col2 = st.columns(2)
            name = col1.text_input("Subcounty Name *")
            code = col2.text_input("Code (optional)")
            if st.form_submit_button("Add Subcounty", use_container_width=True):
                if not name.strip():
                    st.error("Name is required.")
                else:
                    ok, msg = execute_write(
                        "INSERT INTO subcounties (name, code) VALUES (:name, :code)",
                        {"name": name.strip(), "code": code.strip() or None},
                    )
                    if ok:
                        st.success(f"✅ Subcounty '{name}' added.")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

        # Delete subcounty
        if not sc_df.empty:
            st.markdown("---")
            st.markdown("**Delete Subcounty**")
            with st.form("delete_subcounty"):
                del_id = st.selectbox(
                    "Select subcounty to delete",
                    options=sc_df['id'].tolist(),
                    format_func=lambda x: sc_df.loc[
                        sc_df['id'] == x, 'name'
                    ].values[0],
                    key="delete_sc_select",
                )
                st.caption(
                    "⚠️ Deleting a subcounty will also remove its wards "
                    "and unlink projects associated with it."
                )
                if st.form_submit_button("Delete Subcounty", type="primary"):
                    ok, msg = execute_write(
                        "DELETE FROM subcounties WHERE id = :id", {"id": del_id}
                    )
                    if ok:
                        st.success("✅ Subcounty deleted.")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

    # =====================================================
    # WARDS
    # =====================================================
    with tab2:
        st.subheader("Manage Wards")

        wards_df = run_query("""
            SELECT w.id, w.name, s.name AS subcounty
            FROM wards w
            JOIN subcounties s ON w.subcounty_id = s.id
            ORDER BY s.name, w.name
        """)

        if wards_df.empty:
            st.info("No wards yet. Add one below.")
        else:
            st.dataframe(wards_df, use_container_width=True, hide_index=True)

        sc_options = run_query("SELECT id, name FROM subcounties ORDER BY name")

        if sc_options.empty:
            st.warning("⚠️ Add subcounties first before adding wards.")
        else:
            st.markdown("**Add New Ward**")
            with st.form("add_ward", clear_on_submit=True):
                col1, col2 = st.columns(2)
                ward_name = col1.text_input("Ward Name *")
                sc_id = col2.selectbox(
                    "Subcounty *",
                    options=sc_options['id'].tolist(),
                    format_func=lambda x: sc_options.loc[
                        sc_options['id'] == x, 'name'
                    ].values[0],
                )
                if st.form_submit_button("Add Ward", use_container_width=True):
                    if not ward_name.strip():
                        st.error("Ward name is required.")
                    else:
                        ok, msg = execute_write(
                            "INSERT INTO wards (name, subcounty_id) VALUES (:name, :sc)",
                            {"name": ward_name.strip(), "sc": sc_id},
                        )
                        if ok:
                            st.success(f"✅ Ward '{ward_name}' added.")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")

            # Delete ward
            if not wards_df.empty:
                st.markdown("---")
                st.markdown("**Delete Ward**")
                with st.form("delete_ward"):
                    del_ward_id = st.selectbox(
                        "Select ward to delete",
                        options=wards_df['id'].tolist(),
                        format_func=lambda x: (
                            f"{wards_df.loc[wards_df['id'] == x, 'subcounty'].values[0]}"
                            f" — {wards_df.loc[wards_df['id'] == x, 'name'].values[0]}"
                        ),
                        key="delete_ward_select",
                    )
                    if st.form_submit_button("Delete Ward", type="primary"):
                        ok, msg = execute_write(
                            "DELETE FROM wards WHERE id = :id", {"id": del_ward_id}
                        )
                        if ok:
                            st.success("✅ Ward deleted.")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")

    # =====================================================
    # DEPARTMENTS
    # =====================================================
    with tab3:
        st.subheader("Manage Departments")

        dept_df = run_query(
            "SELECT id, name, description FROM departments ORDER BY name"
        )

        if dept_df.empty:
            st.info("No departments yet. Add one below.")
        else:
            st.dataframe(dept_df, use_container_width=True, hide_index=True)

        st.markdown("**Add New Department**")
        with st.form("add_department", clear_on_submit=True):
            dept_name = st.text_input("Department Name *")
            dept_desc = st.text_area("Description (optional)")
            if st.form_submit_button("Add Department", use_container_width=True):
                if not dept_name.strip():
                    st.error("Name is required.")
                else:
                    ok, msg = execute_write(
                        """INSERT INTO departments (name, description)
                           VALUES (:name, :desc)""",
                        {
                            "name": dept_name.strip(),
                            "desc": dept_desc.strip() or None,
                        },
                    )
                    if ok:
                        st.success(f"✅ Department '{dept_name}' added.")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

        # Delete department
        if not dept_df.empty:
            st.markdown("---")
            st.markdown("**Delete Department**")
            with st.form("delete_department"):
                del_dept_id = st.selectbox(
                    "Select department to delete",
                    options=dept_df['id'].tolist(),
                    format_func=lambda x: dept_df.loc[
                        dept_df['id'] == x, 'name'
                    ].values[0],
                    key="delete_dept_select",
                )
                if st.form_submit_button("Delete Department", type="primary"):
                    ok, msg = execute_write(
                        "DELETE FROM departments WHERE id = :id",
                        {"id": del_dept_id},
                    )
                    if ok:
                        st.success("✅ Department deleted.")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
