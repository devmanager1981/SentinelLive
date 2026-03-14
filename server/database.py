import os
from google.cloud import firestore
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID", "glive-build")
DATABASE_ID = os.getenv("GOOGLE_FIRESTORE_DB", "glive-fire-db")

# Initialize Firestore client
db = firestore.Client(project=PROJECT_ID, database=DATABASE_ID)

def get_db():
    return db
