import streamlit as st
import hashlib
from utils.db import run_query, execute_write

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate(username: str, password: str) -> dict:
    """Verify credentials and return user record if valid."""
    users = run_query(
        "SELECT id, username, role FROM users WHERE username = :u AND password_hash = :p",
        {"u": username, "p": hash_password(password)}
    )
    return users.iloc[0].to_dict() if not users.empty else None

# Session state for auth
if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    st.subheader("Login")
    with st.form("login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            user = authenticate(username, password)
            if user:
                st.session_state.user = user
                st.rerun()
            else:
                st.error("Invalid credentials")
else:
    st.subheader(f"User Management — Logged in as {st.session_state.user['username']}")
    # Admin-only user CRUD here
