import streamlit as st
import pandas as pd

def get_connection():
    """Initialize and return a Neon connection."""
    return st.connection("neon", type="sql")

def run_query(query, params=None, ttl="1m"):
    """Execute a SELECT query and return a DataFrame."""
    conn = get_connection()
    return conn.query(query, params=params, ttl=ttl)

def execute_write(query, params=None):
    """Execute INSERT/UPDATE/DELETE and return success status."""
    conn = get_connection()
    try:
        with conn.session as session:
            session.execute(query, params or {})
            session.commit()
        return True, "Operation successful"
    except Exception as e:
        return False, str(e)
