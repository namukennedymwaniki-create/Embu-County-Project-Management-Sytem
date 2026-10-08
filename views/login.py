"""
Login view — Embu County Project Management System.
Full-screen branded authentication page.
"""

import streamlit as st
import base64
from pathlib import Path
from datetime import datetime
import bcrypt

from utils.db import run_query, execute_write


def _load_logo_b64() -> str:
    logo_path = Path("assets/embu_logo.png")
    if logo_path.exists():
        try:
            return base64.b64encode(logo_path.read_bytes()).decode()
        except Exception:
            return ""
    return ""


def _verify_credentials(username: str, password: str):
    """Return user dict if valid, else None. Also checks is_active."""
    try:
        df = run_query(
            """
            SELECT id, username, email, password_hash, role,
                   full_name, is_active
            FROM users
            WHERE username = :u
            LIMIT 1
            """,
            {"u": username.strip()},
            ttl=0,  # never cache auth lookups
        )
    except Exception as e:
        return None, f"Database error: {e}"

    if df.empty:
        return None, "Invalid username or password."

    row = df.iloc[0].to_dict()

    if not row.get("is_active", True):
        return None, "This account has been deactivated. Contact your administrator."

    stored_hash = row["password_hash"]
    try:
        if isinstance(stored_hash, str):
            stored_hash = stored_hash.encode()
        if not bcrypt.checkpw(password.encode(), stored_hash):
            return None, "Invalid username or password."
    except Exception:
        return None, "Invalid username or password."

    # Success — return user without the hash
    row.pop("password_hash", None)
    return row, None


def _update_last_login(user_id: int):
    try:
        execute_write(
            "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = :id",
            {"id": user_id},
        )
    except Exception:
        pass  # not fatal


def render():
    """Render the login page. Returns nothing — sets st.session_state.user on success."""

    logo_b64 = _load_logo_b64()

    # =====================================================
    # FULL-SCREEN STYLING
    # =====================================================
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

            html, body, [class*="css"] {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont,
                             'Segoe UI', sans-serif;
            }

            /* Hide sidebar & header chrome on login */
            section[data-testid="stSidebar"] { display: none !important; }
            header[data-testid="stHeader"] { display: none !important; }

            /* Dark full-screen background */
            .stApp {
                background:
                    radial-gradient(circle at 20% 20%,
                        rgba(234,179,8,0.08) 0%, transparent 40%),
                    radial-gradient(circle at 80% 80%,
                        rgba(59,130,246,0.06) 0%, transparent 40%),
                    linear-gradient(135deg, #0b1220 0%, #0f172a 50%, #111827 100%);
            }

            .block-container {
                padding-top: 4rem !important;
                padding-bottom: 2rem !important;
                max-width: 100% !important;
            }

            /* Login card styling */
            .login-card {
                background: linear-gradient(145deg,
                            rgba(255,255,255,0.04) 0%,
                            rgba(255,255,255,0.02) 100%);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 20px;
                padding: 40px 36px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.4);
                backdrop-filter: blur(20px);
            }

            /* Streamlit text inputs inside the card */
            section.main .stTextInput > div > div > input {
                background: rgba(255,255,255,0.04) !important;
                border: 1px solid rgba(255,255,255,0.10) !important;
                color: #e2e8f0 !important;
                border-radius: 10px !important;
                padding: 12px 14px !important;
                font-size: 14px !important;
            }
            section.main .stTextInput > div > div > input:focus {
                border-color: #eab308 !important;
                box-shadow: 0 0 0 3px rgba(234,179,8,0.15) !important;
            }
            section.main .stTextInput label {
                color: #94a3b8 !important;
                font-size: 12px !important;
                font-weight: 600 !important;
                letter-spacing: 0.5px !important;
                text-transform: uppercase !important;
            }

            /* Primary button = gold gradient */
            section.main .stButton > button[kind="primary"],
            section.main .stFormSubmitButton > button {
                width: 100%;
                background: linear-gradient(135deg, #eab308 0%, #b45309 100%) !important;
                color: #0f172a !important;
                font-weight: 700 !important;
                font-size: 14px !important;
                padding: 12px 16px !important;
                border: none !important;
                border-radius: 10px !important;
                letter-spacing: 0.3px !important;
                box-shadow: 0 4px 14px rgba(234,179,8,0.30) !important;
                transition: all 0.2s ease !important;
            }
            section.main .stButton > button[kind="primary"]:hover,
            section.main .stFormSubmitButton > button:hover {
                transform: translateY(-1px);
                box-shadow: 0 6px 20px rgba(234,179,8,0.45) !important;
            }

            /* Alerts polish */
            section.main .stAlert {
                border-radius: 10px !important;
            }
        </style>
    """, unsafe_allow_html=True)

    # =====================================================
    # CENTERED LAYOUT
    # =====================================================
    spacer_left, center, spacer_right = st.columns([1, 1.1, 1])

    with center:
        # ---- Logo block ----
        if logo_b64:
            st.markdown(f"""
                <div style="text-align:center; margin-bottom: 28px;">
                    <div style="
                        width: 92px; height: 92px;
                        background: white;
                        border-radius: 50%;
                        display: inline-flex;
                        align-items: center; justify-content: center;
                        box-shadow: 0 8px 30px rgba(234,179,8,0.40),
                                    inset 0 0 0 4px rgba(234,179,8,0.35);
                        overflow: hidden;
                        padding: 8px;
                    ">
                        <img src="data:image/png;base64,{logo_b64}"
                             style="width:100%; height:100%; object-fit:contain;" />
                    </div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div style="text-align:center; margin-bottom:28px;">
                    <div style="font-size:56px;">🏛️</div>
                </div>
            """, unsafe_allow_html=True)

        # ---- Titles ----
        st.markdown("""
            <div style="text-align:center; margin-bottom: 30px;">
                <div style="
                    font-size: 24px; font-weight: 800; color: #ffffff;
                    letter-spacing: 0.5px; line-height: 1.3;
                ">
                    Embu County Project Management System
                </div>
                <div style="
                    font-size: 13px; color: #94a3b8; margin-top: 8px;
                    letter-spacing: 0.3px;
                ">
                    Sign in to access the county dashboard
                </div>
            </div>
        """, unsafe_allow_html=True)

        # ---- Login form ----
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input(
                "Username",
                placeholder="Enter your username",
                key="login_username",
            )
            password = st.text_input(
                "Password",
                placeholder="Enter your password",
                type="password",
                key="login_password",
            )

            st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

            submitted = st.form_submit_button(
                "🔐  Sign In",
                use_container_width=True,
                type="primary",
            )

            if submitted:
                if not username.strip() or not password:
                    st.error("Please enter both username and password.")
                else:
                    user, err = _verify_credentials(username, password)
                    if user:
                        _update_last_login(user["id"])
                        st.session_state.user = user
                        st.session_state.current_page = "Dashboard"
                        st.success(f"Welcome back, {user.get('full_name') or user['username']}!")
                        st.rerun()
                    else:
                        st.error(err or "Login failed.")

        # ---- Help footer ----
        st.markdown("""
            <div style="
                text-align: center; margin-top: 24px;
                font-size: 11px; color: #64748b; line-height: 1.7;
            ">
                🔒 Protected system · Unauthorized access is prohibited<br>
                For access requests, contact the County ICT Administrator
            </div>
        """, unsafe_allow_html=True)

        # ---- Version / copyright ----
        st.markdown(f"""
            <div style="
                text-align: center; margin-top: 40px;
                font-size: 10px; color: #475569;
                letter-spacing: 0.5px;
            ">
                © {datetime.now().year} Embu County Government ·
                Land of Opportunities · v1.0.0
            </div>
        """, unsafe_allow_html=True)
