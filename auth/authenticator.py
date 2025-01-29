import time
import streamlit as st
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from auth.token_manager import AuthTokenManager

class Authenticator:
    def __init__(
        self,
        allowed_users: list,
        secret_path: str,
        redirect_uri: str,
        token_key: str,
        cookie_name: str = "auth_jwt",
        token_duration_days: int = 1,
    ):
        st.session_state["connected"] = st.session_state.get("connected", False)
        self.allowed_users = allowed_users
        self.secret_path = secret_path
        self.redirect_uri = redirect_uri
        self.auth_token_manager = AuthTokenManager(
            cookie_name=cookie_name,
            token_key=token_key,
            token_duration_days=token_duration_days,
        )
        self.cookie_name = cookie_name

    def _initialize_flow(self) -> google_auth_oauthlib.flow.Flow:
        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            self.secret_path,
            scopes=[
                "openid",
                "https://www.googleapis.com/auth/userinfo.profile",
                "https://www.googleapis.com/auth/userinfo.email",
            ],
            redirect_uri=self.redirect_uri,
        )
        return flow

    def get_auth_url(self) -> str:
        flow = self._initialize_flow()
        auth_url, _ = flow.authorization_url(
            access_type="offline", include_granted_scopes="true"
        )
        return auth_url

    def login(self):
        if not st.session_state["connected"]:
            auth_url = self.get_auth_url()
            # st.link_button("login with google", auth_url)
            st.markdown(
                f"""
                <style>
                .gcenter {{
                    width: 100%;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                }}
                </style>
                <div class="gcenter">
                    <a href="{auth_url}" target="_self">
                        <button style="background-color: #4285F4; margin-right:15px; color: white; border-radius: 5px; padding: 10px 50px; font-size: 20px; border: none; cursor: pointer;">
                            Login with Google
                            <img src="https://icon2.cleanpng.com/lnd/20241121/sc/bd7ce03eb1225083f951fc01171835.webp" 
                            width="30" style="vertical-align: middle; margin-left: 10px; border-radius: 50%;"/>
                        </button>
                    </a>
                </div>
                """,
                unsafe_allow_html=True
            )

    def check_auth(self):
        if st.session_state["connected"]:
            if not st.session_state["login_message_shown"]:
                st.success("Login successful!")
                st.session_state["login_message_shown"] = True
            return

        if st.session_state.get("logout"):
            st.toast(":green[Logout successful]")
            return

        token = self.auth_token_manager.get_decoded_token()
        if token is not None:
            
            st.query_params.clear()
            st.session_state["connected"] = True
            st.session_state["user_info"] = {
                "email": token["email"],
                "oauth_id": token["oauth_id"],
            }
            st.rerun()  # update session state

        time.sleep(1)  # important for the token to be set correctly

        auth_code = st.query_params.get("code")
        st.query_params.clear()
        if auth_code:
            flow = self._initialize_flow()
            flow.fetch_token(code=auth_code)
            creds = flow.credentials

            oauth_service = build(serviceName="oauth2", version="v2", credentials=creds)
            user_info = oauth_service.userinfo().get().execute()
            oauth_id = user_info.get("id")
            email = user_info.get("email")
            self.auth_token_manager.set_token(email, oauth_id)
            st.session_state["connected"] = True
            st.session_state["user_info"] = {
                "oauth_id": oauth_id,
                "email": email,
            }

            # no rerun

    def logout(self):
        st.session_state["logout"] = True
        st.session_state["user_info"] = None
        st.session_state["connected"] = None
        self.auth_token_manager.delete_token()
        # no rerun