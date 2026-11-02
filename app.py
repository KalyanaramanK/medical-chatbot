from flask import Flask, render_template, jsonify, request
from src.helper import download_hugging_face_embeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
try:
    from langchain.chains import create_retrieval_chain
    from langchain.chains.combine_documents import create_stuff_documents_chain
except ModuleNotFoundError:
    from langchain_classic.chains import create_retrieval_chain
    from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from src.prompt import *
import os

app = Flask(__name__)

load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
QDRANT_URL = os.environ.get("QDRANT_URL")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY")
COLLECTION_NAME = "medical-chatbot"
FRONTEND_ORIGINS = {
    origin.strip().rstrip("/")
    for origin in os.environ.get(
        "FRONTEND_ORIGINS",
        "https://chatbot-887c5.web.app,https://chatbot-887c5.firebaseapp.com,"
        "http://localhost:8080,http://127.0.0.1:8080",
    ).split(",")
    if origin.strip()
}

rag_chain = None
init_status = "Standby"
init_error = None

try:
    # 1. Initialize Qdrant Client (Cloud if URL provided, otherwise local disk)
    if QDRANT_URL:
        print(f"Connecting to Qdrant Cloud at {QDRANT_URL}...")
        qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    else:
        qdrant_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "qdrant_db")
        if os.path.exists(qdrant_path):
            print(f"Loading local Qdrant database from: {qdrant_path}")
            qdrant_client = QdrantClient(path=qdrant_path)
        else:
            qdrant_client = None
            print("Notice: Local 'qdrant_db' directory does not exist yet. Run 'store_index.py' to generate it.")

    # 2. Initialize LLM (prefer Groq AI)
    chat_model = None
    llm_name = None
    if GROQ_API_KEY:
        print(f"Initializing Groq AI ({GROQ_MODEL})...")
        chat_model = ChatGroq(
            model=GROQ_MODEL,
            groq_api_key=GROQ_API_KEY,
            temperature=0.3
        )
        llm_name = f"Groq ({GROQ_MODEL})"
    elif OPENAI_API_KEY:
        print("Initializing OpenAI (gpt-4o)...")
        chat_model = ChatOpenAI(model="gpt-4o", api_key=OPENAI_API_KEY)
        llm_name = "OpenAI (gpt-4o)"
    else:
        print("Notice: No GROQ_API_KEY or OPENAI_API_KEY found.")

    # 3. Assemble RAG pipeline if both Qdrant collection and LLM are ready
    if qdrant_client and qdrant_client.collection_exists(COLLECTION_NAME) and chat_model:
        embeddings = download_hugging_face_embeddings()
        docsearch = QdrantVectorStore(
            client=qdrant_client,
            collection_name=COLLECTION_NAME,
            embedding=embeddings,
        )
        retriever = docsearch.as_retriever(search_type="similarity", search_kwargs={"k": 3})
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", "{input}"),
            ]
        )
        question_answer_chain = create_stuff_documents_chain(chat_model, prompt)
        rag_chain = create_retrieval_chain(retriever, question_answer_chain)
        init_status = f"Active ({llm_name} + Qdrant)"
        print(f"RAG chain successfully activated with {init_status}!")
    else:
        reasons = []
        if not chat_model:
            reasons.append("Missing GROQ_API_KEY in .env")
        if not qdrant_client or not qdrant_client.collection_exists(COLLECTION_NAME):
            reasons.append("Qdrant collection not indexed yet (run store_index.py)")
        init_status = "Standby: " + ", ".join(reasons)
        print(f"RAG in standby mode: {init_status}")

except Exception as e:
    init_error = str(e)
    print(f"Error during RAG initialization: {e}")


@app.route("/")
def index():
    return render_template("chat.html")


@app.route("/health")
def health():
    return jsonify(status="ok")


@app.after_request
def add_cors_headers(response):
    origin = request.headers.get("Origin", "").rstrip("/")
    if origin in FRONTEND_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.vary.add("Origin")
    return response


@app.route("/get", methods=["GET", "POST"])
def chat():
    msg = request.form.get("msg", "")
    print(f"User Query: {msg}")

    if rag_chain is not None:
        try:
            response = rag_chain.invoke({"input": msg})
            print("Response generated successfully.")
            return str(response["answer"])
        except Exception as e:
            return f"Error executing query: {e}"

    # Standby guidance message
    return (
        "<b>Medical Chatbot (Standby Mode)</b><br><br>"
        "To enable live medical answers with Qdrant & Groq AI:<br>"
        "1. Open <code>.env</code> and add your <code>GROQ_API_KEY</code> (get a free key at <a href='https://console.groq.com/keys' target='_blank'>console.groq.com</a>).<br>"
        "2. Run <code>python store_index.py</code> to index the medical book into Qdrant.<br>"
        "3. Restart the server.<br><br>"
        f"<i>Current Status: {init_status}</i>"
        + (f"<br><i>Details: {init_error}</i>" if init_error else "")
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True, use_reloader=False)
