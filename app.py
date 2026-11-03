import logging
import os
from flask import Flask, Response, render_template, jsonify, request
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
from src.prompt import system_prompt

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 8192
MAX_QUESTION_LENGTH = 2000
logger = logging.getLogger(__name__)

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
        logger.info("Connecting to Qdrant Cloud")
        qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    else:
        qdrant_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "qdrant_db")
        if os.path.exists(qdrant_path):
            logger.info("Loading local Qdrant database")
            qdrant_client = QdrantClient(path=qdrant_path)
        else:
            qdrant_client = None
            logger.info("Local Qdrant database is not present")

    # 2. Initialize LLM (prefer Groq AI)
    chat_model = None
    llm_name = None
    if GROQ_API_KEY:
        logger.info("Initializing Groq model")
        chat_model = ChatGroq(
            model=GROQ_MODEL,
            groq_api_key=GROQ_API_KEY,
            temperature=0.3
        )
        llm_name = f"Groq ({GROQ_MODEL})"
    elif OPENAI_API_KEY:
        logger.info("Initializing OpenAI model")
        chat_model = ChatOpenAI(model="gpt-4o", api_key=OPENAI_API_KEY)
        llm_name = "OpenAI (gpt-4o)"
    else:
        logger.info("No supported model API key is configured")

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
        logger.info("RAG chain initialized")
    else:
        reasons = []
        if not chat_model:
            reasons.append("No model API key configured")
        if not qdrant_client or not qdrant_client.collection_exists(COLLECTION_NAME):
            reasons.append("Qdrant collection not indexed yet (run store_index.py)")
        init_status = "Standby: " + ", ".join(reasons)
        logger.info("RAG is in standby mode: %s", init_status)

except Exception as error:
    init_error = type(error).__name__
    logger.error("RAG initialization failed (%s)", init_error)


@app.route("/")
def index():
    return render_template("chat.html")


@app.route("/health")
def health():
    return jsonify(status="ok", rag_ready=rag_chain is not None)


@app.route("/ready")
def ready():
    if rag_chain is None:
        return jsonify(status="not_ready"), 503
    return jsonify(status="ready")


@app.after_request
def add_cors_headers(response):
    origin = request.headers.get("Origin", "").rstrip("/")
    if origin in FRONTEND_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.vary.add("Origin")
    return response


@app.errorhandler(413)
def request_too_large(_error):
    return Response("Request body is too large.", status=413, mimetype="text/plain")


@app.route("/get", methods=["POST"])
def chat():
    msg = request.form.get("msg", "").strip()
    if not msg:
        return Response("Please enter a question.", status=400, mimetype="text/plain")
    if len(msg) > MAX_QUESTION_LENGTH:
        return Response(
            f"Questions must be {MAX_QUESTION_LENGTH} characters or fewer.",
            status=400,
            mimetype="text/plain",
        )

    if rag_chain is not None:
        try:
            response = rag_chain.invoke({"input": msg})
            answer = response.get("answer")
            if not isinstance(answer, str) or not answer.strip():
                raise ValueError("The model returned an empty answer")
            return Response(answer, mimetype="text/plain")
        except Exception as error:
            logger.error("RAG request failed (%s)", type(error).__name__)
            return Response(
                "The chatbot could not complete this request. Please try again later.",
                status=502,
                mimetype="text/plain",
            )

    # Keep initialization details out of the public response.
    return Response(
        "The chatbot is not ready. Please try again later.",
        status=503,
        mimetype="text/plain",
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False, use_reloader=False)
