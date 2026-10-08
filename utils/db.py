import streamlit as st

def get_connection():
    try:
        return st.connection("neon", type="sql")
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        st.stop()

def run_query(query, params=None, ttl="1m"):
    conn = get_connection()
    return conn.query(query, params=params, ttl=ttl)

def execute_write(query, params=None):
    conn = get_connection()
    try:
        with conn.session as session:
            session.execute(query, params or {})
            session.commit()
        return True, "Operation successful"
    except Exception as e:
        return False, str(e)
