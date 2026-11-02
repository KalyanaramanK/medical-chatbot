from firebase_functions import https_fn
from firebase_functions.options import MemoryOption
from firebase_functions.params import SecretParam
from app import app

GROQ_API_KEY = SecretParam("GROQ_API_KEY")
QDRANT_URL = SecretParam("QDRANT_URL")
QDRANT_API_KEY = SecretParam("QDRANT_API_KEY")

# Firebase Cloud Functions (2nd Gen) HTTPS entry point for Flask
@https_fn.on_request(
    memory=MemoryOption.GB_2,
    timeout_sec=300,
    secrets=[GROQ_API_KEY, QDRANT_URL, QDRANT_API_KEY],
)
def chatbot(req: https_fn.Request) -> https_fn.Response:
    return https_fn.Response.from_app(app, req)
