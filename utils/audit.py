"""
Audit trail helper — Embu County Project Management System.
Records every meaningful action performed in the system.
"""

import json
import streamlit as st
from sqlalchemy import text
from utils.db import get_connection


def _get_current_user():
    """Return the current user dict from session state, if signed in."""
    return st.session_state.get("user") or {}


def _jsonify(value):
    """Make a value JSON-safe for storage in a JSONB column."""
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "isoformat"):          # date / datetime
        return value.isoformat()
    return str(value)


def _clean_dict(d):
    """Convert a row/dict into a JSON-safe dictionary."""
    if d is None:
        return None
    if hasattr(d, "to_dict"):
        d = d.to_dict()
    return {k: _jsonify(v) for k, v in d.items()}


def log_action(
    action: str,
    table_name: str,
    record_id: int = None,
    record_label: str = None,
    old_values: dict = None,
    new_values: dict = None,
    notes: str = None,
):
    """
    Insert a row into audit_logs.

    Parameters
    ----------
    action : str
        One of CREATE, UPDATE, DELETE, LOGIN, LOGOUT, IMPORT, EXPORT, VIEW, OTHER.
    table_name : str
        Affected table (e.g., 'projects', 'users') or 'auth' for login events.
    record_id : int, optional
        Primary key of the affected record.
    record_label : str, optional
        A human-readable identifier (e.g., project name).
    old_values : dict, optional
        Snapshot of the record BEFORE the change (for UPDATE/DELETE).
    new_values : dict, optional
        Snapshot of the record AFTER the change (for CREATE/UPDATE).
    notes : str, optional
        Additional context.
    """
    try:
        user = _get_current_user()
        conn = get_connection()

        # Compute the diff for UPDATE actions
        changes = None
        if action == "UPDATE" and old_values and new_values:
            changes = {}
            for k in set(old_values) | set(new_values):
                before = _jsonify(old_values.get(k))
                after = _jsonify(new_values.get(k))
                if before != after:
                    changes[k] = {"from": before, "to": after}

        params = {
            "user_id": user.get("id"),
            "username": user.get("username", "system"),
            "user_role": user.get("role", "system"),
            "action": action,
            "table_name": table_name,
            "record_id": record_id,
            "record_label": record_label,
            "changes": json.dumps(changes) if changes else None,
            "old_values": json.dumps(_clean_dict(old_values)) if old_values else None,
            "new_values": json.dumps(_clean_dict(new_values)) if new_values else None,
            "notes": notes,
        }

        with conn.session as session:
            session.execute(
                text("""
                    INSERT INTO audit_logs
                        (user_id, username, user_role, action, table_name,
                         record_id, record_label, changes, old_values,
                         new_values, notes)
                    VALUES
                        (:user_id, :username, :user_role, :action, :table_name,
                         :record_id, :record_label, CAST(:changes AS JSONB),
                         CAST(:old_values AS JSONB), CAST(:new_values AS JSONB),
                         :notes)
                """),
                params,
            )
            session.commit()

    except Exception as e:
        # Never let auditing break the main flow
        try:
            st.warning(f"⚠️ Audit log warning: {e}")
        except Exception:
            pass


# =====================================================
# CONVENIENCE WRAPPERS
# =====================================================
def log_create(table_name, record_id, record_label, new_values):
    log_action(
        action="CREATE",
        table_name=table_name,
        record_id=record_id,
        record_label=record_label,
        new_values=new_values,
    )


def log_update(table_name, record_id, record_label, old_values, new_values):
    log_action(
        action="UPDATE",
        table_name=table_name,
        record_id=record_id,
        record_label=record_label,
        old_values=old_values,
        new_values=new_values,
    )


def log_delete(table_name, record_id, record_label, old_values):
    log_action(
        action="DELETE",
        table_name=table_name,
        record_id=record_id,
        record_label=record_label,
        old_values=old_values,
    )


def log_login(username, user_id=None, success=True):
    log_action(
        action="LOGIN",
        table_name="auth",
        record_id=user_id,
        record_label=username,
        notes="Success" if success else "Failed login attempt",
    )


def log_logout(username, user_id=None):
    log_action(
        action="LOGOUT",
        table_name="auth",
        record_id=user_id,
        record_label=username,
    )


def log_import(table_name, record_count, notes=None):
    log_action(
        action="IMPORT",
        table_name=table_name,
        notes=notes or f"Bulk imported {record_count} record(s)",
    )


def log_export(table_name, record_count, notes=None):
    log_action(
        action="EXPORT",
        table_name=table_name,
        notes=notes or f"Exported {record_count} record(s)",
    )
