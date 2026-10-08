"""
Users view — Embu County Project Management System.
Manage system users and role-based access.
"""

import streamlit as st
import bcrypt
from utils.db import run_query, execute_write


def render():
    st.title("👥 User Management")
    st.caption("Manage system users and role-based access")
    st.markdown("---")

    # =====================================================
    # LOAD USERS
    # =====================================================
    users_df = run_query("""
        SELECT id, username, email, role, created_at
        FROM users
        ORDER BY id DESC
    """)

    # =====================================================
    # EXISTING USERS
    # =====================================================
    st.subheader("📑 Existing Users")

    if users_df.empty:
        st.info("No users yet. Add one below.")
    else:
        st.dataframe(
            users_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": st.column_config.NumberColumn("ID", width="small"),
                "username": "Username",
                "email": "Email",
                "role": st.column_config.SelectboxColumn(
                    "Role",
                    options=["viewer", "editor", "admin"],
                    required=True,
                ),
                "created_at": st.column_config.DatetimeColumn(
                    "Created", format="DD MMM YYYY, HH:mm"
                ),
            },
        )

    st.markdown("---")

    # =====================================================
    # ADD USER
    # =====================================================
    st.subheader("➕ Add New User")

    with st.form("add_user", clear_on_submit=True):
        col1, col2 = st.columns(2)
        username = col1.text_input("Username *")
        email = col2.text_input("Email *")
        password = col1.text_input("Password *", type="password")
        confirm = col1.text_input("Confirm Password *", type="password")
        role = col2.selectbox("Role *", ["viewer", "editor", "admin"])

        submitted = st.form_submit_button("Create User", use_container_width=True)

        if submitted:
            if not username.strip() or not email.strip() or not password:
                st.error("All fields are required.")
            elif password != confirm:
                st.error("Passwords do not match.")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters.")
            else:
                pwd_hash = bcrypt.hashpw(
                    password.encode(), bcrypt.gensalt()
                ).decode()
                ok, msg = execute_write(
                    """INSERT INTO users (username, email, password_hash, role)
                       VALUES (:u, :e, :p, :r)""",
                    {
                        "u": username.strip(),
                        "e": email.strip(),
                        "p": pwd_hash,
                        "r": role,
                    },
                )
                if ok:
                    st.success(f"✅ User '{username}' created.")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")

    st.markdown("---")

    # =====================================================
    # UPDATE USER
    # =====================================================
    if not users_df.empty:
        st.subheader("✏️ Update User")

        with st.expander("Edit an existing user", expanded=False):
            edit_user_id = st.selectbox(
                "Select user to edit",
                options=users_df['id'].tolist(),
                format_func=lambda x: f"#{x} — "
                f"{users_df.loc[users_df['id'] == x, 'username'].values[0]}",
                key="edit_user_select",
            )

            current_user = users_df[users_df['id'] == edit_user_id].iloc[0]

            with st.form("edit_user"):
                col1, col2 = st.columns(2)
                new_username = col1.text_input(
                    "Username", value=current_user['username']
                )
                new_email = col2.text_input(
                    "Email", value=current_user['email']
                )

                roles = ["viewer", "editor", "admin"]
                role_index = roles.index(current_user['role']) \
                    if current_user['role'] in roles else 0
                new_role = col2.selectbox("Role", roles, index=role_index)

                new_password = col1.text_input(
                    "New Password (leave blank to keep current)",
                    type="password",
                )

                if st.form_submit_button(
                    "💾 Update User", use_container_width=True
                ):
                    if not new_username.strip() or not new_email.strip():
                        st.error("Username and email are required.")
                    else:
                        if new_password:
                            pwd_hash = bcrypt.hashpw(
                                new_password.encode(), bcrypt.gensalt()
                            ).decode()
                            ok, msg = execute_write(
                                """UPDATE users
                                   SET username = :u, email = :e,
                                       password_hash = :p, role = :r
                                   WHERE id = :id""",
                                {
                                    "u": new_username.strip(),
                                    "e": new_email.strip(),
                                    "p": pwd_hash,
                                    "r": new_role,
                                    "id": edit_user_id,
                                },
                            )
                        else:
                            ok, msg = execute_write(
                                """UPDATE users
                                   SET username = :u, email = :e, role = :r
                                   WHERE id = :id""",
                                {
                                    "u": new_username.strip(),
                                    "e": new_email.strip(),
                                    "r": new_role,
                                    "id": edit_user_id,
                                },
                            )
                        if ok:
                            st.success(f"✅ User #{edit_user_id} updated.")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")

        st.markdown("---")

        # =====================================================
        # DELETE USER
        # =====================================================
        st.subheader("🗑️ Delete User")

        with st.expander("Delete a user", expanded=False):
            del_user_id = st.selectbox(
                "Select user to delete",
                options=users_df['id'].tolist(),
                format_func=lambda x: f"#{x} — "
                f"{users_df.loc[users_df['id'] == x, 'username'].values[0]}",
                key="delete_user_select",
            )

            confirm_del = st.checkbox(
                f"I confirm I want to permanently delete user #{del_user_id}",
                key="delete_user_confirm",
            )

            if st.button(
                "Delete User",
                type="primary",
                disabled=not confirm_del,
                use_container_width=True,
            ):
                ok, msg = execute_write(
                    "DELETE FROM users WHERE id = :id", {"id": del_user_id}
                )
                if ok:
                    st.success(f"✅ User #{del_user_id} deleted.")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")
