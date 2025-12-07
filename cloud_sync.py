import streamlit as st
import json
import base64
from firebase_admin import credentials, firestore, initialize_app


def init_firebase():
    """Initializes Firebase connection using credentials stored in Streamlit secrets."""
    # Avoid initializing firebase multiple times
    if "firebase_app" not in st.session_state:

        if "firebase_credentials" not in st.secrets:
            raise Exception("Firebase credentials key missing in Streamlit secrets.")

        # Decode Base64 firebase key
        try:
            key_b64 = st.secrets["firebase_credentials"]
            key_json = json.loads(base64.b64decode(key_b64).decode("utf-8"))
        except Exception as e:
            raise Exception(f"Failed to decode Firebase credentials: {e}")

        cred = credentials.Certificate(key_json)
        firebase_app = initialize_app(cred)

        st.session_state.firebase_app = firebase_app
        st.session_state.firestore_db = firestore.client()


# ---- SAVE LOCAL DATA ----
# **SYNTAX FIX applied here:** The function signature was corrected.
def save_local_data(data, file_path="local_data.json"):
    """Saves data dictionary to a local JSON file."""
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)


# ---- LOAD LOCAL DATA ----
# This function is named restore_data, which loads the data.
def restore_data(file_path="local_data.json"):
    """Loads data dictionary from a local JSON file, returns empty dict if file not found."""
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        # Returning {} instead of None to match load_data's original logic in app.py
        return {}


# ---- MANUAL CLOUD SYNC (Push to Firebase) ----
def manual_sync():
    """Manually pushes local_data from session state to Firestore."""
    init_firebase()
    db = st.session_state.firestore_db
    # This function uses a hardcoded user ID: "default_user"
    doc_ref = db.collection("users").document("default_user")

    if "local_data" in st.session_state:
        doc_ref.set(st.session_state.local_data)
        st.success("☁️ Data manually synced to cloud!")
        return "Manual sync complete."
    else:
        st.warning("No local data found in session state to sync.")
        return "Manual sync skipped."


# ---- AUTO SYNC (Pull from Firebase) ----
def auto_sync():
    """Pulls data from Firestore and overwrites st.session_state.local_data."""
    init_firebase()
    db = st.session_state.firestore_db
    # This function uses a hardcoded user ID: "default_user"
    doc = db.collection("users").document("default_user").get()

    if doc.exists:
        st.session_state.local_data = doc.to_dict()
        st.info("🔄 Auto-sync completed from cloud!")
        return "Auto sync complete."
    else:
        st.info("No cloud data found. Initializing with empty dictionary.")
        return "Auto sync skipped."
