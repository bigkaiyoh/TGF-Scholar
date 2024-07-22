import firebase_admin
from firebase_admin import credentials
from google.cloud import secretmanager

def get_secret(secret_id):
    client = secretmanager.SecretManagerServiceClient()
    name = f"{secret_id}/versions/latest"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode("UTF-8")

firebase_creds = get_secret("projects/581656499945/secrets/firebase-service-account-key")

cred = credentials.Certificate(firebase_creds)
firebase_admin.initialize_app(cred)
