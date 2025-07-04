import streamlit as st
from common import authenticator
from stream import home_page
from EmailCrm import *
from NewsSummary import *


# emails of users that are allowed to login
# st.set_page_config(layout="wide", page_title="Bond Analytics")


if "connected" not in st.session_state:
    st.session_state["connected"] = False
    
if "login_message_shown" not in st.session_state:
    st.session_state["login_message_shown"] = False

# st.title("Bond Analytics")



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
 # Dictionary to map app name to the app module's run function
    APP_MAP = {
        "Email CRM":email_crm_gmail_run,
        "News Summarizer": news_app,
        "Email CRM (Domain)":email_crm_outreach_chintanthakkar_run,
        "Bond Analytics":home_page
    }

    # st.set_page_config(page_title="Streamlit Multi-App", layout="wide")
    # st.sidebar.title("🧭 Choose an App")

    # Sidebar dropdown to select app
    selected_app = st.sidebar.selectbox("Select an application", list(APP_MAP.keys()))

    # Run the selected app
    APP_MAP[selected_app]()