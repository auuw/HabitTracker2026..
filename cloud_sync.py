# cloud_sync.py
import json
import os
import firebase_admin
from firebase_admin import credentials, firestore

LOCAL_FILE = "local_data.json"

# Initialize Firebase once (requires serviceAccountKey.json in same folder)
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()


def load_local_data():
    if not os.path.exists(LOCAL_FILE):
        return None
    with open(LOCAL_FILE, "r") as f:
        return json.load(f)


def save_local_data(obj):
    with open(LOCAL_FILE, "w") as f:
        json.dump(obj, f, indent=2)


def manual_sync(user_id):
    """Push local_data.json to Firestore under users/{user_id}/backups/full_backup"""
    data = load_local_data()
    if data is None:
        return "⚠ No local data to sync."
    try:
        db.collection("users").document(user_id).collection("backups").document("full_backup").set(data)
        db.collection("users").document(user_id).collection("meta").document("last_sync").set({"ts": firestore.SERVER_TIMESTAMP})
        return "☁ Full backup synced to cloud."
    except Exception as e:
        return "❌ Sync failed: " + str(e)


def auto_sync(user_id, summary=None):
    """Save a small summary (used after changes). summary is a dict -> stored in users/{user_id}/autosync"""
    try:
        payload = summary or {"last_sync": True}
        db.collection("users").document(user_id).collection("backups").document("autosync").set(payload, merge=True)
        return "Auto-sync OK"
    except Exception as e:
        return "Auto-sync failed: " + str(e)


def restore_data(user_id):
    """Restore full_backup to local file (overwrite local_data.json)"""
    try:
        doc = db.collection("users").document(user_id).collection("backups").document("full_backup").get()
        if doc.exists:
            data = doc.to_dict()
            save_local_data(data)
            return "📥 Restored data from cloud (local overwritten)."
        else:
            return "⚠ No cloud backup found."
    except Exception as e:
        return "❌ Restore failed: " + str(e)



