import os
from pathlib import Path

ROOT = Path(__file__).parent.parent

# Auth
LOCAL_DEV      = os.getenv("LOCAL_DEV", "false").lower() == "true"
TOKEN_KEY      = os.getenv("TOKEN_KEY", "dev-secret-change-me")
ALLOWED_USERS  = [e.strip() for e in os.getenv("ALLOWED_USERS", "").split(",") if e.strip()]
ADMINS         = [e.strip() for e in os.getenv("ADMINS", "").split(",") if e.strip()]

# Google OAuth
GOOGLE_CLIENT_ID     = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
OAUTH_REDIRECT_URI   = os.getenv("OAUTH_REDIRECT_URI", "http://localhost:8000/api/auth/callback")

# External API keys
FRED_API_KEY       = os.getenv("FRED_API_KEY", "")
NEWS_API_KEY       = os.getenv("NEWS_API_KEY", "")
COHERE_API_KEY     = os.getenv("COHERE_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# Data files
FINAL_XLSX    = ROOT / "Final.xlsx"
