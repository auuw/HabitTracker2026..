import streamlit as st
import json
import base64
from firebase_admin import credentials, firestore, initialize_app

# Load Firebase key from Streamlit secrets
encoded_key = st.secrets.get("FIREBASE_KEY")

if not encoded_key:
    st.error("❌ Firebase key not found in secrets!")
    firebase_dict = None
else:
    firebase_json = base64.b64decode(encoded_key).decode("utf-8")
    firebase_dict = json.loads(firebase_json)

# Initialize Firebase
db = None
if firebase_dict and not len(firebase_dict) == 0:
    cred = credentials.Certificate(firebase_dict)
    try:
        initialize_app(cred)
    except ValueError:
        pass
    db = firestore.client()




