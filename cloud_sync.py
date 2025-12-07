import base64
import json
from firebase_admin import credentials, firestore, initialize_app
import streamlit as st

def init_firebase():
    if "firebase_app" not in st.session_state:
        key_b64 = st.secrets["firebase"]["credentials"]
        key_json = json.loads(base64.b64decode(key_b64).decode("utf-8"))
        cred = credentials.Certificate(key_json)
        st.session_state.firebase_app = initialize_app(cred)
        st.session_state.db = firestore.client()




