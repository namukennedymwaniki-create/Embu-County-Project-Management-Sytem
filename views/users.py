"""Users — Manage system users and roles."""

import streamlit as st
import bcrypt
from utils.db import run_query, execute_write

def render():
    st.title("👥 User Management")
    
st.title("👥 User Management")
st.caption("Manage system users and role-based access")
st.markdown("---")

# ---------------- LIST USERS ----------------
users_df = run_query("""
    SELECT id, username, email, role, created_at
    FROM users
    ORDER BY id DESC
""")

st.subheader("Existing Users")
if users_df.empty:
    st.info("No users yet. Add one below.")
else:
    st.dataframe(users_df, use_container_width=True, hide_index=True)

st.markdown("---")

# ---------------- ADD USER ----------------
st.subheader("➕ Add New User")

with st.form("add_user", clear_on_submit=True):
    col1, col2 = st.columns(2)
    username = col1.text_input("Username *")
    email = col2.text_input("Email *")
    password = col1.text_input("Password *", type="password")
    role = col2.selectbox("Role *", ["viewer", "editor", "admin"])

    if st.form_submit_button("Create User", use_container_width=True):
        if not username.strip() or not email.strip() or not password:
            st.error("All fields are required.")
        else:
            pwd_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
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
                st.success(f"User '{username}' created.")
                st.cache_data.clear()
                st.rerun()
            else:
                st.error(msg)

st.markdown("---")

# ---------------- DELETE USER ----------------
if not users_df.empty:
    st.subheader("🗑️ Delete User")
    with st.form("delete_user"):
        del_id = st.selectbox(
            "Select user to remove",
            options=users_df['id'].tolist(),
            format_func=lambda x: f"#{x} — "
            f"{users_df.loc[users_df['id'] == x, 'username'].values[0]}",
        )
        if st.form_submit_button("Delete User", type="primary"):
            ok, msg = execute_write(
                "DELETE FROM users WHERE id = :id", {"id": del_id}
            )
            if ok:
                st.success(f"User #{del_id} deleted.")
                st.cache_data.clear()
                st.rerun()
            else:
                st.error(msg)
