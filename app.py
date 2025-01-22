import streamlit as st
from common import authenticator
from stream import home_page


# emails of users that are allowed to login
st.set_page_config(layout="wide", page_title="Bond Analytics")


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
 home_page()