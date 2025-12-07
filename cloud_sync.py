import json
import base64
import os

firebase_key = os.environ.get("FIREBASE_KEY")

if firebase_key:
    firebase_dict = json.loads(base64.b64decode(firebase_key).decode("utf-8"))
    cred = credentials.Certificate(firebase_dict)
else:
    raise Exception("Firebase key missing in Streamlit secrets!")




