"""
Embu County Project Management System
Main entry — login gate + professional sidebar + module router.
"""

import streamlit as st
import base64
from pathlib import Path

# =====================================================
# PAGE CONFIG (must be first Streamlit call)
# =====================================================
st.set_page_config(
    page_title="Embu County PMS",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =====================================================
# AUTH GATE — show login page if not authenticated
# =====================================================
if "user" not in st.session_state or st.session_state.user is None:
    from views import login
    login.render()
    st.stop()

# =====================================================
# GLOBAL CSS (only after login)
# =====================================================
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont,
                         'Segoe UI', Roboto, sans-serif;
        }

        [data-testid="stSidebarNav"] { display: none; }
        [data-testid="stSidebarNavItems"] { display: none; }

        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg,
                        #0b1220 0%, #111827 60%, #0f172a 100%);
            border-right: 1px solid rgba(255,255,255,0.05);
        }
        section[data-testid="stSidebar"] > div:first-child {
            padding-top: 1.2rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }

        section[data-testid="stSidebar"] .stButton > button {
            width: 100%;
            text-align: left;
            justify-content: flex-start;
            padding: 12px 16px;
            margin-bottom: 6px;
            border-radius: 10px;
            border: 1px solid transparent;
            background: transparent;
            color: #cbd5e1;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.15s ease;
            letter-spacing: 0.2px;
        }
        section[data-testid="stSidebar"] .stButton > button:hover {
            background: rgba(234,179,8,0.08);
            border-color: rgba(234,179,8,0.25);
            color: #ffffff;
        }
        section[data-testid="stSidebar"] .stButton > button:focus {
            outline: none; box-shadow: none;
        }
        section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
            background: linear-gradient(135deg,
                        rgba(234,179,8,0.18) 0%,
                        rgba(234,179,8,0.06) 100%);
            border-color: rgba(234,179,8,0.45);
            color: #ffffff;
            font-weight: 600;
            box-shadow: inset 3px 0 0 0 #eab308;
        }

        section[data-testid="stSidebar"] hr {
            margin: 12px 0;
            border-color: rgba(255,255,255,0.06);
        }

        .sidebar-section-label {
            font-size: 10px;
            font-weight: 700;
            color: #64748b;
            letter-spacing: 1.4px;
            text-transform: uppercase;
            margin: 16px 4px 8px;
        }

        .sidebar-footer {
            margin-top: 12px;
            padding: 14px 14px;
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 12px;
            font-size: 11px;
            color: #94a3b8;
            line-height: 1.5;
        }
        .sidebar-footer strong { color: #e2e8f0; }
        .sidebar-footer .badge {
            display: inline-block;
            padding: 2px 8px;
            background: rgba(234,179,8,0.15);
            color: #eab308;
            border-radius: 6px;
            font-size: 10px;
            font-weight: 600;
            margin-left: 4px;
        }

        h1, h2, h3 { letter-spacing: -0.3px; }
        .block-container { padding-top: 2rem; }
    </style>
""", unsafe_allow_html=True)

# =====================================================
# LOAD LOGO
# =====================================================
logo_b64 = ""
logo_path = Path("assets/embu_logo.png")
if logo_path.exists():
    try:
        logo_b64 = base64.b64encode(logo_path.read_bytes()).decode()
    except Exception:
        logo_b64 = ""

# =====================================================
# SIDEBAR — HEADER, MODULES, ACCOUNT
# =====================================================
with st.sidebar:

    # ---------- BRANDED HEADER ----------
    if logo_b64:
        st.markdown(f"""
            <div style="
                text-align: center;
                padding: 22px 16px 20px;
                background: linear-gradient(135deg,
                            rgba(234,179,8,0.10) 0%,
                            rgba(234,179,8,0.02) 100%);
                border: 1px solid rgba(234,179,8,0.18);
                border-radius: 16px;
                margin-bottom: 6px;
            ">
                <div style="
                    width: 78px; height: 78px;
                    background: #ffffff;
                    border-radius: 50%;
                    display: flex; align-items: center;
                    justify-content: center;
                    margin: 0 auto 14px auto;
                    box-shadow: 0 6px 20px rgba(234,179,8,0.35),
                                inset 0 0 0 3px rgba(234,179,8,0.35);
                    overflow: hidden; padding: 6px;
                ">
                    <img src="data:image/png;base64,{logo_b64}"
                         style="width:100%; height:100%; object-fit:contain;" />
                </div>
                <div style="font-size: 17px; font-weight: 800; color: #ffffff;
                            letter-spacing: 1px;">
                    EMBU COUNTY
                </div>
                <div style="font-size: 12px; font-weight: 600; color: #eab308;
                            margin-top: 4px; letter-spacing: 0.3px;">
                    Project Management System
                </div>
                <div style="
                    display: inline-block;
                    margin-top: 10px; padding: 3px 10px;
                    background: rgba(255,255,255,0.05);
                    border: 1px solid rgba(255,255,255,0.08);
                    border-radius: 20px;
                    font-size: 10px; color: #94a3b8;
                    letter-spacing: 0.5px;
                ">
                    Land of Opportunities
                </div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div style="text-align:center; padding:22px 16px;
                        background:rgba(234,179,8,0.08);
                        border:1px solid rgba(234,179,8,0.18);
                        border-radius:16px; margin-bottom:6px;">
                <div style="font-size:36px;">🏛️</div>
                <div style="font-size:17px; font-weight:800; color:#ffffff;
                            letter-spacing:1px; margin-top:8px;">
                    EMBU COUNTY
                </div>
                <div style="font-size:12px; font-weight:600; color:#eab308;
                            margin-top:4px;">
                    Project Management System
                </div>
            </div>
        """, unsafe_allow_html=True)

    # ---------- MODULES ----------
    st.markdown(
        '<div class="sidebar-section-label">Modules</div>',
        unsafe_allow_html=True,
    )

    # Role-based page visibility
    user_role = (st.session_state.user or {}).get("role", "viewer")

    PAGES = {
        "Dashboard": ("🏠", ["viewer", "editor", "admin"]),
        "Projects":  ("📋", ["viewer", "editor", "admin"]),
        "Settings":  ("⚙️", ["admin"]),
        "Users":     ("👥", ["admin"]),
    }

    if "current_page" not in st.session_state:
        st.session_state.current_page = "Dashboard"

    # If current page isn't allowed for this role, fall back to Dashboard
    if user_role not in PAGES.get(st.session_state.current_page, ("", []))[1]:
        st.session_state.current_page = "Dashboard"

    for page_name, (icon, allowed_roles) in PAGES.items():
        if user_role not in allowed_roles:
            continue
        is_active = st.session_state.current_page == page_name
        if st.button(
            f"{icon}   {page_name}",
            key=f"nav_{page_name}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
        ):
            st.session_state.current_page = page_name
            st.rerun()

    # ---------- ACCOUNT FOOTER ----------
    st.markdown(
        '<div class="sidebar-section-label">Account</div>',
        unsafe_allow_html=True,
    )

    user = st.session_state.user
    if user:
        display_name = user.get("full_name") or user.get("username", "User")
        initial = display_name[0].upper() if display_name else "?"
        role = (user.get("role") or "viewer").title()

        st.markdown(f"""
            <div class="sidebar-footer">
                <div style="display:flex; align-items:center; gap:10px;">
                    <div style="
                        width:32px; height:32px; border-radius:50%;
                        background: linear-gradient(135deg,#eab308,#b45309);
                        display:flex; align-items:center;
                        justify-content:center;
                        color:#0f172a; font-weight:800; font-size:13px;
                        flex-shrink:0;
                    ">
                        {initial}
                    </div>
                    <div style="flex:1; overflow:hidden;">
                        <div style="color:#e2e8f0; font-weight:600;
                                    font-size:12px; white-space:nowrap;
                                    overflow:hidden; text-overflow:ellipsis;">
                            {display_name}
                        </div>
                        <div style="font-size:10px; color:#94a3b8;">
                            {role} <span class="badge">●</span>
                        </div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        if st.button("🚪   Sign Out",
                     key="nav_signout",
                     use_container_width=True):
            st.session_state.user = None
            st.session_state.current_page = "Dashboard"
            st.rerun()

# =====================================================
# ROUTER
# =====================================================
page = st.session_state.current_page

try:
    if page == "Dashboard":
        from views import dashboard
        dashboard.render()
    elif page == "Projects":
        from views import projects
        projects.render()
    elif page == "Settings":
        from views import settings
        settings.render()
    elif page == "Users":
        from views import users
        users.render()
    else:
        st.error(f"Unknown page: {page}")
        st.session_state.current_page = "Dashboard"
        st.rerun()
except ModuleNotFoundError as e:
    st.error(
        f"⚠️ Missing module: {e}. "
        "Ensure `views/__init__.py` and `utils/__init__.py` exist."
    )
except Exception as e:
    st.error(f"⚠️ Error rendering **{page}**: {e}")
