import json
from google.cloud import firestore, secretmanager
import firebase_admin
from firebase_admin import credentials

def get_firebase_creds():
    client = secretmanager.SecretManagerServiceClient()
    secret_name = "projects/581656499945/secrets/firebase-service-account-key/versions/latest"
    response = client.access_secret_version(request={"name": secret_name})
    secret_string = response.payload.data.decode("UTF-8")
    return json.loads(secret_string)

firebase_creds = get_firebase_creds()

# Initialize Firebase Admin SDK with the credentials
cred = credentials.Certificate(firebase_creds)
firebase_admin.initialize_app(cred)

# Initialize Firestore DB
db = firestore.client()
