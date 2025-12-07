import streamlit as st
import json
import base64
from firebase_admin import credentials, firestore, initialize_app


def init_firebase():
    # Avoid initializing firebase multiple times
    if "firebase_app" not in st.session_state:

        if "firebase_credentials" not in st.secrets:
            raise Exception("Firebase credentials key missing in Streamlit secrets.")

        # Decode Base64 firebase key
        key_b64 = st.secrets["firebase_credentials"]
        key_json = json.loads(base64.b64decode(key_b64).decode("utf-8"))

        cred = credentials.Certificate(key_json)
        firebase_app = initialize_app(cred)

        st.session_state.firebase_app = firebase_app
        st.session_state.firestore_db = firestore.client()


# ---- SAVE LOCAL DATA ----
def save_local_data(data, file_path="local_data.json"):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)


# ---- LOAD LOCAL DATA ----
def restore_data():
    try:
        with open("local_data.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


# ---- MANUAL CLOUD SYNC ----
def manual_sync():
    init_firebase()
    db = st.session_state.firestore_db
    doc = db.collection("users").document("default_user")

    if "local_data" in st.session_state:
        doc.set(st.session_state.local_data)
        st.success("☁️ Data manually synced to cloud!")


# ---- AUTO SYNC (Pull from Firebase) ----
def auto_sync():
    init_firebase()
    db = st.session_state.firestore_db
    doc = db.collection("users").document("default_user").get()

    if doc.exists:
        st.session_state.local_data = doc.to_dict()
        st.info("🔄 Auto-sync completed from cloud!")


