import firebase_admin
from firebase_admin import credentials, firestore

# Path to your Firebase service account key file
cred = credentials.Certificate("unicke-firebase-adminsdk-l7s4j-d04bf19ccb.json")
firebase_admin.initialize_app(cred)

# Initialize Firestore
db = firestore.client()
