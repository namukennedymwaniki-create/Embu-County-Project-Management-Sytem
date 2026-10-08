"""
Embu County Project Management System
Main entry point — renders branded sidebar header + module navigation.
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
# SIDEBAR HEADER (above the modules)
# =====================================================
logo_b64 = ""
logo_path = Path("assets/embu_logo.png")
if logo_path.exists():
    logo_b64 = base64.b64encode(logo_path.read_bytes()).decode()

with st.sidebar:
    if logo_b64:
        st.markdown(f"""
            <div style="
                text-align: center;
                padding: 20px 12px;
                margin-bottom: 20px;
                background: rgba(255,255,255,0.06);
                border-radius: 16px;
                border: 1px solid rgba(255,255,255,0.08);
            ">
                <div style="
                    width: 72px; height: 72px;
                    background: white;
                    border-radius: 50%;
                    display: flex; align-items: center; justify-content: center;
                    margin: 0 auto 12px auto;
                    box-shadow: 0 4px 12px rgba(212,175,55,0.35);
                    overflow: hidden; padding: 6px;
                ">
                    <img src="data:image/png;base64,{logo_b64}"
                         style="width: 100%; height: 100%; object-fit: contain;" />
                </div>
                <div style="font-size: 16px; font-weight: 700; color: white; letter-spacing: 0.5px;">
                    EMBU COUNTY
                </div>
                <div style="font-size: 12px; font-weight: 600; color: #eab308; margin-top: 4px;">
                    Project Management System
                </div>
                <div style="font-size: 10px; color: #94a3b8; margin-top: 8px;
                            padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.05);">
                    Land of Opportunities
                </div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div style="text-align: center; padding: 20px 12px; margin-bottom: 20px;
                        background: rgba(255,255,255,0.06); border-radius: 16px;
                        border: 1px solid rgba(255,255,255,0.08);">
                <div style="font-size: 32px;">🏛️</div>
                <div style="font-size: 16px; font-weight: 700; color: white;
                            letter-spacing: 0.5px; margin-top: 8px;">
                    EMBU COUNTY
                </div>
                <div style="font-size: 12px; font-weight: 600; color: #eab308; margin-top: 4px;">
                    Project Management System
                </div>
            </div>
        """, unsafe_allow_html=True)

# =====================================================
# MODULE NAVIGATION (renders below the header)
# =====================================================
pages = {
    "Modules": [
        st.Page("views/dashboard.py", title="Dashboard", icon="🏠", default=True),
        st.Page("views/projects.py",  title="Projects",  icon="📋"),
        st.Page("views/settings.py",  title="Settings",  icon="⚙️"),
        st.Page("views/users.py",     title="Users",     icon="👥"),
    ],
}

pg = st.navigation(pages)
pg.run()
