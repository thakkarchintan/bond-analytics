import firebase_admin
from firebase_admin import credentials, firestore, get_app
import os
import json

def firebase_config():
    try:
        # Check if Firebase app is already initialized
        get_app()
    except ValueError:
        # Initialize only if not already initialized
        if "FIREBASE_KEY_JSON" in os.environ:
            # For Render or deployed env
            cred_dict = json.loads(os.environ["FIREBASE_KEY_JSON"])
            cred = credentials.Certificate(cred_dict)
        else:
            # For local development
            cred = credentials.Certificate("serviceAccountKey.json")

        firebase_admin.initialize_app(cred)

    # Always safe to return Firestore client
    return firestore.client()
