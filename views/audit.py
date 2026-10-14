"""
Audit Trail view — Embu County Project Management System.
Displays all system activity with filtering and drill-down.
"""

import json
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

from utils.db import run_query


# =====================================================
# HELPERS
# =====================================================
ACTION_COLORS = {
    "CREATE":  ("#065f46", "#d1fae5"),   # green
    "UPDATE":  ("#1e40af", "#dbeafe"),   # blue
    "DELETE":  ("#991b1b", "#fee2e2"),   # red
    "LOGIN":   ("#5b21b6", "#ede9fe"),   # purple
    "LOGOUT":  ("#374151", "#e5e7eb"),   # gray
    "IMPORT":  ("#92400e", "#fef3c7"),   # amber
    "EXPORT":  ("#155e75", "#cffafe"),   # cyan
    "VIEW":    ("#374151", "#e5e7eb"),   # gray
    "OTHER":   ("#374151", "#e5e7eb"),   # gray
}

ACTION_ICONS = {
    "CREATE":  "➕",
    "UPDATE":  "✏️",
    "DELETE":  "🗑️",
    "LOGIN":   "🔐",
    "LOGOUT":  "🚪",
    "IMPORT":  "📥",
    "EXPORT":  "📤",
    "VIEW":    "👁️",
    "OTHER":   "•",
}


def _action_badge(action):
    fg, bg = ACTION_COLORS.get(action, ("#374151", "#e5e7eb"))
    icon = ACTION_ICONS.get(action, "")
    return (
        f'<span style="background:{bg}; color:{fg}; padding:4px 10px; '
        f'border-radius:10px; font-size:11px; font-weight:600; '
        f'white-space:nowrap;">{icon} {action}</span>'
    )


def _fmt_ts(ts):
    if ts is None or pd.isna(ts):
        return "—"
    try:
        return pd.to_datetime(ts).strftime("%d %b %Y · %H:%M:%S")
    except Exception:
        return str(ts)


def _safe_json_load(value):
    """Parse a JSONB field returned as str or dict."""
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return None


def _humanize_changes(changes):
    """Turn a changes dict into a readable list of 'field: old → new'."""
    if not changes:
        return []
    lines = []
    for field, delta in changes.items():
        if isinstance(delta, dict) and "from" in delta and "to" in delta:
            old = delta["from"]
            new = delta["to"]
            lines.append(
                f"**{field.replace('_', ' ').title()}**: "
                f"`{old if old is not None else '—'}` → "
                f"`{new if new is not None else '—'}`"
            )
        else:
            lines.append(f"**{field}**: {delta}")
    return lines


# =====================================================
# MAIN RENDER
# =====================================================
def render():
    st.title("🔍 Audit Trail")
    st.caption("Complete record of every action taken in the system")
    st.markdown("---")

    # ---- Load reference lookups ----
    try:
        users_df = run_query("SELECT id, username FROM users ORDER BY username")
    except Exception:
        users_df = pd.DataFrame(columns=["id", "username"])

    # =====================================================
    # FILTER BAR
    # =====================================================
    with st.container(border=True):
        st.markdown(
            "<div style='font-size:12px; font-weight:600; color:#64748b; "
            "text-transform:uppercase; letter-spacing:0.5px; "
            "margin-bottom:10px;'>🎛️ Filters</div>",
            unsafe_allow_html=True,
        )

        f1, f2, f3, f4 = st.columns([1, 1, 1, 1])

        # Date range
        date_preset = f1.selectbox(
            "Date Range",
            [
                "Last 24 hours",
                "Last 7 days",
                "Last 30 days",
                "Last 90 days",
                "All time",
                "Custom range",
            ],
            index=2,
            key="audit_date_preset",
        )

        now = datetime.now()
        if date_preset == "Last 24 hours":
            default_from = now - timedelta(days=1)
            default_to = now
        elif date_preset == "Last 7 days":
            default_from = now - timedelta(days=7)
            default_to = now
        elif date_preset == "Last 30 days":
            default_from = now - timedelta(days=30)
            default_to = now
        elif date_preset == "Last 90 days":
            default_from = now - timedelta(days=90)
            default_to = now
        elif date_preset == "All time":
            default_from = now - timedelta(days=3650)
            default_to = now
        else:
            default_from = now - timedelta(days=30)
            default_to = now

        if date_preset == "Custom range":
            date_from = f1.date_input("From", value=default_from.date())
            date_to = f1.date_input("To", value=default_to.date())
        else:
            date_from = default_from.date()
            date_to = default_to.date()

        action_options = [
            "All Actions",
            "CREATE", "UPDATE", "DELETE",
            "LOGIN", "LOGOUT", "IMPORT", "EXPORT", "OTHER",
        ]
        selected_action = f2.selectbox(
            "Action", action_options, key="audit_action_filter"
        )

        table_options = [
            "All Tables",
            "projects", "subcounties", "wards", "departments",
            "users", "auth",
        ]
        selected_table = f3.selectbox(
            "Table", table_options, key="audit_table_filter"
        )

        user_options = ["All Users"] + users_df['username'].tolist()
        selected_user = f4.selectbox(
            "User", user_options, key="audit_user_filter"
        )

        # Search box
        search = st.text_input(
            "🔍 Search record label, notes, or username",
            placeholder="Type to search...",
            key="audit_search",
        )

        col_r1, col_r2 = st.columns([1, 5])
        if col_r1.button(
            "🔄 Reset Filters",
            use_container_width=True,
            key="audit_reset",
        ):
            for k in [
                "audit_date_preset", "audit_action_filter",
                "audit_table_filter", "audit_user_filter",
                "audit_search",
            ]:
                st.session_state.pop(k, None)
            st.rerun()

    # =====================================================
    # BUILD QUERY
    # =====================================================
    where = ["created_at::date BETWEEN :d1 AND :d2"]
    params = {
        "d1": date_from.isoformat(),
        "d2": date_to.isoformat(),
    }

    if selected_action != "All Actions":
        where.append("action = :action")
        params["action"] = selected_action

    if selected_table != "All Tables":
        where.append("table_name = :table_name")
        params["table_name"] = selected_table

    if selected_user != "All Users":
        where.append("username = :username")
        params["username"] = selected_user

    if search.strip():
        where.append(
            "(record_label ILIKE :search "
            "OR notes ILIKE :search "
            "OR username ILIKE :search)"
        )
        params["search"] = f"%{search.strip()}%"

    where_sql = " AND ".join(where)

    try:
        logs_df = run_query(
            f"""
            SELECT
                id, user_id, username, user_role, action, table_name,
                record_id, record_label, changes, old_values, new_values,
                notes, created_at
            FROM audit_logs
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT 5000
            """,
            params=params,
            ttl=0,
        )
    except Exception as e:
        st.error(f"⚠️ Could not load audit logs: {e}")
        return

    # =====================================================
    # SUMMARY METRICS
    # =====================================================
    total = len(logs_df)
    creates = len(logs_df[logs_df['action'] == 'CREATE']) if total else 0
    updates = len(logs_df[logs_df['action'] == 'UPDATE']) if total else 0
    deletes = len(logs_df[logs_df['action'] == 'DELETE']) if total else 0
    logins = len(logs_df[logs_df['action'] == 'LOGIN']) if total else 0

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("📋 Total Events", f"{total:,}")
    m2.metric("➕ Creates", f"{creates:,}")
    m3.metric("✏️ Updates", f"{updates:,}")
    m4.metric("🗑️ Deletes", f"{deletes:,}")
    m5.metric("🔐 Logins", f"{logins:,}")

    st.markdown("---")

    if logs_df.empty:
        st.info("📭 No audit events match the current filters.")
        return

    # =====================================================
    # EVENTS TABLE
    # =====================================================
    st.markdown(f"### 📜 Event Log ({total:,} events)")

    display = logs_df.copy()
    display['Action'] = display['action'].apply(
        lambda a: f"{ACTION_ICONS.get(a,'')} {a}"
    )
    display['Timestamp'] = display['created_at'].apply(_fmt_ts)
    display['User'] = display.apply(
        lambda r: f"{r['username']} ({r['user_role']})"
        if r['user_role'] else r['username'],
        axis=1,
    )
    display['Record'] = display.apply(
        lambda r: f"{r['table_name']}#{r['record_id']}"
        if pd.notna(r['record_id']) and r['record_id'] is not None
        else r['table_name'],
        axis=1,
    )
    display = display[[
        'Timestamp', 'Action', 'User', 'Record',
        'record_label', 'notes',
    ]].rename(columns={
        'record_label': 'Record Label',
        'notes': 'Notes',
    })

    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
        height=420,
        column_config={
            "Timestamp": st.column_config.TextColumn("Timestamp", width="small"),
            "Action": st.column_config.TextColumn("Action", width="small"),
            "User": st.column_config.TextColumn("User", width="medium"),
            "Record": st.column_config.TextColumn("Record", width="small"),
            "Record Label": st.column_config.TextColumn(
                "Record Label", width="medium"
            ),
            "Notes": st.column_config.TextColumn("Notes", width="medium"),
        },
    )

    # =====================================================
    # EVENT DETAIL INSPECTOR
    # =====================================================
    st.markdown("---")
    st.markdown("### 🔎 Event Details")

    # Build a selection label list
    options = logs_df.apply(
        lambda r: (
            f"#{r['id']} · {_fmt_ts(r['created_at'])} · "
            f"{r['action']} · {r['username']}"
        ),
        axis=1,
    ).tolist()

    selected_label = st.selectbox(
        "Select an event to inspect",
        options=options,
        key="audit_detail_select",
        label_visibility="collapsed",
    )

    selected_id = int(selected_label.split(" ")[0].replace("#", ""))
    event = logs_df[logs_df['id'] == selected_id].iloc[0]

    with st.container(border=True):
        # Header
        h1, h2 = st.columns([3, 1])
        with h1:
            st.markdown(
                f"#### {ACTION_ICONS.get(event['action'],'')} "
                f"{event['action']} · {event['table_name']}"
            )
            st.caption(
                f"Event #{event['id']} · {_fmt_ts(event['created_at'])}"
            )
        with h2:
            st.markdown(
                f"<div style='text-align:right;'>"
                f"{_action_badge(event['action'])}</div>",
                unsafe_allow_html=True,
            )

        st.markdown("---")

        # Key info
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"**👤 User**  \n{event['username'] or '—'}")
        c2.markdown(f"**🎭 Role**  \n{event['user_role'] or '—'}")
        c3.markdown(
            f"**🆔 Record**  \n"
            f"{event['table_name']}"
            f"{'#' + str(event['record_id']) if event['record_id'] else ''}"
        )

        if event['record_label']:
            st.markdown(f"**🏷️ Record Label**  \n{event['record_label']}")

        if event['notes']:
            st.markdown(f"**📝 Notes**  \n{event['notes']}")

        # Changes (UPDATE)
        changes = _safe_json_load(event['changes'])
        if changes:
            st.markdown("---")
            st.markdown("##### 📊 Changes")
            for line in _humanize_changes(changes):
                st.markdown(f"- {line}")

        # Old / new values (CREATE, DELETE, UPDATE)
        old_vals = _safe_json_load(event['old_values'])
        new_vals = _safe_json_load(event['new_values'])

        if old_vals or new_vals:
            st.markdown("---")
            st.markdown("##### 🔍 Full Snapshot")
            vcol1, vcol2 = st.columns(2)

            with vcol1:
                st.markdown("**Before**")
                if old_vals:
                    st.json(old_vals, expanded=True)
                else:
                    st.caption("_No prior values_")

            with vcol2:
                st.markdown("**After**")
                if new_vals:
                    st.json(new_vals, expanded=True)
                else:
                    st.caption("_No new values_")

    # =====================================================
    # EXPORT
    # =====================================================
    st.markdown("---")

    export_df = logs_df.copy()
    csv = export_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download Audit Log (CSV)",
        data=csv,
        file_name=(
            f"embu_audit_{date_from.isoformat()}_to_{date_to.isoformat()}.csv"
        ),
        mime="text/csv",
    )

    st.caption(
        f"Showing {total:,} events · "
        f"Range: {date_from.strftime('%d %b %Y')} → "
        f"{date_to.strftime('%d %b %Y')}"
    )
