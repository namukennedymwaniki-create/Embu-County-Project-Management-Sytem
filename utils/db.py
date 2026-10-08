"""
Database helpers — Embu County Project Management System.
"""

import streamlit as st
from sqlalchemy import text


def get_connection():
    """Initialize and return a Neon connection."""
    try:
        return st.connection("neon", type="sql")
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        st.stop()


def run_query(query, params=None, ttl="1m"):
    """Execute a SELECT query and return a DataFrame."""
    conn = get_connection()
    # Wrap in text() so SQLAlchemy 2.x accepts raw SQL
    return conn.query(text(query), params=params, ttl=ttl)


def execute_write(query, params=None):
    """Execute INSERT / UPDATE / DELETE. Returns (success, message)."""
    conn = get_connection()
    try:
        with conn.session as session:
            session.execute(text(query), params or {})
            session.commit()
        return True, "Operation successful"
    except Exception as e:
        return False, str(e)
