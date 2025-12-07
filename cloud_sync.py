import streamlit as st
import json
import base64
from firebase_admin import credentials, firestore, initialize_app


def init_firebase():
    """Initializes Firebase connection using credentials stored in Streamlit secrets."""
    # Avoid initializing firebase multiple times
    if "firebase_app" not in st.session_state:

        if "firebase_credentials" not in st.secrets:
            # Raising a clear exception if the secret is missing
            raise Exception("Firebase credentials key missing in Streamlit secrets.")

        # Decode Base64 firebase key
        try:
            key_b64 = st.secrets["firebase_credentials"]
            # Ensure the decoded key is a valid JSON string
            key_json = json.loads(base64.b64decode(key_b64).decode("utf-8"))
        except Exception as e:
            raise Exception(f"Failed to decode Firebase credentials: {e}")

        cred = credentials.Certificate(key_json)
        firebase_app = initialize_app(cred)

        # Store the app and the database client in session state
        st.session_state.firebase_app = firebase_app
        st.session_state.firestore_db = firestore.client()


# ---- SAVE LOCAL DATA ----
def save_local_data(data, file_path="local_data.json"):
    """Saves data dictionary to a local JSON file."""
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)


# ---- LOAD LOCAL DATA ----
def restore_data(file_path="local_data.json"):
    """Loads data dictionary from a local JSON file, returns empty dict if file not found."""
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


# ---- MANUAL CLOUD SYNC (Full Push/Pull - Backup Page) ----
def manual_sync(uid, data):
    """Manually pushes full data from provided data to Firestore for the specified user ID."""
    init_firebase()
    db = st.session_state.firestore_db
    doc_ref = db.collection("users").document(uid)

    doc_ref.set(data)
    st.success(f"☁️ Data for user '{uid}' manually synced to cloud!")
    return "Manual sync complete."


# ---- AUTO SYNC (Push Summary - called by save_data) ----
def push_summary(uid, summary):
    """Pushes a small data summary to Firestore for the specified user ID."""
    # If this is called quickly on every save, we don't want to re-initialize firebase every time
    if "firestore_db" not in st.session_state:
        init_firebase()
        
    db = st.session_state.firestore_db
    doc_ref = db.collection("users").document(uid) 
    doc_ref.set(summary, merge=True) # Use merge=True to only update profile/stats


# ---- RESTORE CLOUD DATA (Full Pull - Backup Page) ----
def restore_cloud_data(uid):
    """Pulls full data from Firestore for the specified user ID and returns it."""
    if "firestore_db" not in st.session_state:
        init_firebase()
        
    db = st.session_state.firestore_db
    doc = db.collection("users").document(uid).get()
    
    if doc.exists:
        data = doc.to_dict()
        # Overwrite local data file with cloud data
        save_local_data(data)
        st.info(f"🔄 Full restore for user '{uid}' completed from cloud!")
        return data
    else:
        st.warning("No cloud backup found for this user ID.")
        return None
