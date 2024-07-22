import os
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud import firestore as google_firestore

def initialize_firebase():
    if os.getenv('unicke'):
        # Running on Google Cloud, use Application Default Credentials
        cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred, {
            'projectId': os.getenv('unicke'),
        })
        db = google_firestore.Client()
    else:
        # Local development, use service account key file
        cred = credentials.Certificate("unicke-firebase-adminsdk-l7s4j-d04bf19ccb.json")
        firebase_admin.initialize_app(cred)
        db = firestore.client()
    
    return db

# Initialize Firestore
db = initialize_firebase()