from auth import Authenticator
from dotenv import load_dotenv
import os

load_dotenv()

client_secret_path = "/etc/secrets/client_secret.json" #/etc/secrets/client_secret.json


allowed_users = os.getenv("ALLOWED_USERS").split(",")

authenticator = Authenticator(
    allowed_users=allowed_users,
    token_key=os.getenv("TOKEN_KEY"),
    secret_path=client_secret_path,
    redirect_uri="https://bond-analytics.onrender.com", #https://bond-analytics.onrender.com
)