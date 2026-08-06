from auth import Authenticator
from dotenv import load_dotenv
import os
import tempfile
import streamlit as st

load_dotenv()

_secret_env = os.getenv("GOOGLE_CLIENT_SECRET", "")
# Render sets this to a file path; HF Spaces sets it to raw JSON content.
if _secret_env and not os.path.isfile(_secret_env):
    _tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    _tmp.write(_secret_env)
    _tmp.close()
    client_secret_path = _tmp.name
else:
    client_secret_path = _secret_env


allowed_users = os.getenv("ALLOWED_USERS").split(",")

authenticator = Authenticator(
    allowed_users=allowed_users,
    token_key=os.getenv("TOKEN_KEY"),
    secret_path=client_secret_path,
    redirect_uri=os.getenv("REDIRECT_URI"),
    token_duration_days=3650,
)