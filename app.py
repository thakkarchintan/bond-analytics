import streamlit as st
from common import authenticator
from stream import home_page


# emails of users that are allowed to login
st.set_page_config(layout="wide", page_title="Bond Analytics")

st.title("Bond Analytics")

if "connected" not in st.session_state:
    st.session_state["connected"] = False

authenticator.check_auth()
authenticator.login()
    
# show content that requires login
if st.session_state["connected"]:
    home_page()
if not st.session_state["connected"]:
    st.write("you have to log in first ...")