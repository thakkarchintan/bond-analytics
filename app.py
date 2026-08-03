import streamlit as st
from common import authenticator
from stream import home_page
from HeatmapTab import heatmap_tab
from portfolio_rebalance import portfolio_rebalance
from EmailCrm import *
from NewsSummary import *
from ChangelogTab import changelog_tab
from data import load_data
from dotenv import load_dotenv
import os


def toast_auto_dismiss(message, duration=2000, toast_type="success"):
    bg_colors = {
        "success": "#28a745",
        "error": "#dc3545",
        "info": "#17a2b8",
        "warning": "#ffc107",
    }
    color = bg_colors.get(toast_type, "#28a745")
    st.markdown(
        f"""
        <div id="custom-toast" style="
            position: fixed;
            top: 20px;
            right: 20px;
            background-color: {color};
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
            font-weight: bold;
            z-index: 10000;
        ">
            {message}
        </div>
        <script>
            setTimeout(function() {{
                var toast = document.getElementById("custom-toast");
                if (toast) {{
                    toast.style.display = "none";
                }}
            }}, {duration});
        </script>
        """,
        unsafe_allow_html=True,
    )


st.set_page_config(page_title="Bond Analytics", layout="wide")

if "connected" not in st.session_state:
    st.session_state["connected"] = False

if "login_message_shown" not in st.session_state:
    st.session_state["login_message_shown"] = False

load_dotenv()

if not st.session_state["connected"]:
    st.markdown(
        """
        <style>
        .center {
            display: flex;
            justify-content: center;
            align-items: center;
            margin-top:200px;
        }
        </style>
        <div class="center">
            <h1>Bond Analytics</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

authenticator.check_auth()
authenticator.login()

if st.session_state["connected"]:
    APP_MAP = {
        "News Summarizer": news_app,
        "Bond Analytics": home_page,
        "Correlation Matrix": heatmap_tab,
        "Portfolio Rebalance": portfolio_rebalance,
        "Changelog": changelog_tab,
    }

    if st.sidebar.button("Logout", key="button1"):
        authenticator.logout()

    user_email = st.session_state["user_info"].get("email", "None")
    load_dotenv()

    restricted_apps = ["Email CRM", "Email CRM (Domain)", "Changelog"]
    admins = [email.strip() for email in os.getenv("ADMINS", "").split(",")]

    if "admins" not in st.session_state:
        st.session_state["admins"] = admins

    visible_apps = {
        app_name: app_func
        for app_name, app_func in APP_MAP.items()
        if (app_name not in restricted_apps) or (user_email in admins)
    }

    selected_app = st.sidebar.selectbox("Select an application", list(visible_apps.keys()))

    # Pre-warm the data cache once per session so all tabs respond instantly.
    # load_data() is @st.cache_data — this call pays the Excel load cost here
    # (with a visible spinner) rather than inside a tab where sidebar controls
    # would be frozen while waiting.
    if "data_warmed" not in st.session_state:
        with st.spinner("Loading market data..."):
            load_data()
        st.session_state["data_warmed"] = True

    visible_apps[selected_app]()
