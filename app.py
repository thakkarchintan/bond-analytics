import streamlit as st
from common import authenticator
from stream import home_page
from HeatmapTab import heatmap_tab
from portfolio_rebalance import portfolio_rebalance
from NewsSummary import *
from ChangelogTab import changelog_tab
from MacroDashboard import macro_dashboard
from data import load_data
from dotenv import load_dotenv
import os

# ── Global styles ────────────────────────────────────────────────────────────
_CSS = """
<style>
/* Hide only branding — never touch header/toolbar so sidebar toggle always works */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }

/* Tighter content area */
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
}

/* Dark sidebar */
[data-testid="stSidebar"] {
    background-color: #1e293b;
}
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] span {
    color: #e2e8f0 !important;
}

/* Sidebar selectboxes */
[data-testid="stSidebar"] [data-baseweb="select"] > div:first-child {
    background-color: #334155 !important;
    border-color: #475569 !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] * {
    color: #f1f5f9 !important;
    background-color: #334155 !important;
}

/* Sidebar date inputs */
[data-testid="stSidebar"] input[type="text"],
[data-testid="stSidebar"] input[type="number"] {
    background-color: #334155 !important;
    color: #f1f5f9 !important;
    border-color: #475569 !important;
}

/* Sidebar buttons */
[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    background-color: #334155 !important;
    border: 1px solid #475569 !important;
    color: #f1f5f9 !important;
    border-radius: 6px;
    font-weight: 500;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background-color: #475569 !important;
    border-color: #64748b !important;
}

/* Sidebar slider track */
[data-testid="stSidebar"] [data-testid="stSlider"] div[role="slider"] {
    background-color: #1e40af !important;
}

/* Main area button polish */
.stButton > button {
    border-radius: 6px;
    font-weight: 500;
}

/* Sidebar HR divider */
[data-testid="stSidebar"] hr {
    border-color: #334155;
}
</style>
"""

st.set_page_config(page_title="Bond Analytics", layout="wide")
st.markdown(_CSS, unsafe_allow_html=True)

load_dotenv()

if "connected" not in st.session_state:
    st.session_state["connected"] = False

if "login_message_shown" not in st.session_state:
    st.session_state["login_message_shown"] = False

if not st.session_state["connected"]:
    st.markdown(
        """
        <div style="display:flex; justify-content:center; align-items:center; margin-top:200px;">
            <h1 style="color:#0f172a;">Bond Analytics</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

authenticator.check_auth()
authenticator.login()

if st.session_state["connected"]:
    APP_MAP = {
        "Bond Analytics": home_page,
        "Correlation Matrix": heatmap_tab,
        "Portfolio Rebalance": portfolio_rebalance,
        "News Summarizer": news_app,
        "Global Macro Dashboard": macro_dashboard,
        "Changelog": changelog_tab,
    }

    user_email = st.session_state["user_info"].get("email", "None")

    admins = [email.strip() for email in os.getenv("ADMINS", "").split(",")]
    if "admins" not in st.session_state:
        st.session_state["admins"] = admins

    restricted_apps = ["Changelog"]
    visible_apps = {
        app_name: app_func
        for app_name, app_func in APP_MAP.items()
        if (app_name not in restricted_apps) or (user_email in admins)
    }

    selected_app = st.sidebar.selectbox("Select an application", list(visible_apps.keys()))

    # Pre-warm data cache once per session — pays the Excel load cost here with
    # a spinner so sidebar controls are never frozen inside a tab function.
    if "data_warmed" not in st.session_state:
        with st.spinner("Loading market data..."):
            load_data()
        st.session_state["data_warmed"] = True

    visible_apps[selected_app]()

    # Logout pinned to bottom of sidebar
    st.sidebar.markdown(
        '<hr style="border:none; border-top:1px solid #475569; margin:1.5rem 0 0.75rem;">',
        unsafe_allow_html=True,
    )
    if st.sidebar.button("Logout", key="button1"):
        authenticator.logout()
