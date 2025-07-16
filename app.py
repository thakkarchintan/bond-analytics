import streamlit as st
from common import authenticator
from stream import home_page
from EmailCrm import *
from NewsSummary import *
from dotenv import load_dotenv
import os


def toast_auto_dismiss(message, duration=2000, toast_type="success"):
    bg_colors = {
        "success": "#28a745",
        "error": "#dc3545",
        "info": "#17a2b8",
        "warning": "#ffc107"
    }
    color = bg_colors.get(toast_type, "#28a745")

    st.markdown(f"""
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
    """, unsafe_allow_html=True)

# emails of users that are allowed to login
st.set_page_config(page_title="Streamlit Multi-App", layout="wide")



if "connected" not in st.session_state:
    st.session_state["connected"] = False
    
if "login_message_shown" not in st.session_state:
    st.session_state["login_message_shown"] = False

# st.title("Bond Analytics")

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
        unsafe_allow_html=True
    )


authenticator.check_auth()
authenticator.login()
    
# show content that requires login
if st.session_state["connected"]:
    # APP_MAP = {
    #     "Email CRM":email_crm_gmail_run,
    #     "News Summarizer": news_app,
    #     "Email CRM (Domain)":email_crm_outreach_chintanthakkar_run,
    #     "Bond Analytics":home_page
    # }
    
    # if st.sidebar.button("Logout",key="button1"):
    #     authenticator.logout()

    # selected_app = st.sidebar.selectbox("Select an application", list(APP_MAP.keys()))
    # user_email = st.session_state["user_info"].get("email","None")
    # load_dotenv()

    # # Define restricted apps and allowed users
    # restricted_apps = {
    #     "Email CRM":os.getenv("ADMINS"),
    #     "Email CRM (Domain)":os.getenv("ADMINS")
    # }
    # # Authorization check
    # if selected_app in restricted_apps:
    #     allowed_users = restricted_apps[selected_app]
    #     if user_email in allowed_users:
    #         APP_MAP[selected_app]()
    #     else:
    #         st.error("You do not have permission to access this section.")
    #         st.stop()
    # else:
    #     APP_MAP[selected_app]()
    APP_MAP = {
        "Email CRM": email_crm_gmail_run,
        "News Summarizer": news_app,
        "Email CRM (Domain)": email_crm_outreach_chintanthakkar_run,
        "Bond Analytics": home_page
    }

    if st.sidebar.button("Logout", key="button1"):
        authenticator.logout()

    user_email = st.session_state["user_info"].get("email", "None")
    load_dotenv()

    # Define restricted apps
    # restricted_apps = {
    #     "Email CRM": os.getenv("ADMINS", ""),
    #     "Email CRM (Domain)": os.getenv("ADMINS", "")
    # }
    
    restricted_apps = [ "Email CRM" , "Email CRM (Domain)"]
    admins = [email.strip() for email in os.getenv("ADMINS", "").split(",")]
    
    if "admins" not in st.session_state:
        st.session_state["admins"] = admins

    # Show only allowed apps in dropdown
    visible_apps = {
        app_name: app_func
        for app_name, app_func in APP_MAP.items()
        if (app_name not in restricted_apps) or (user_email in admins)
    }

    selected_app = st.sidebar.selectbox("Select an application", list(visible_apps.keys()))
    visible_apps[selected_app]()
