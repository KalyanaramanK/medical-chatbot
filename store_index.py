import os
import sys
from dotenv import load_dotenv
from src.helper import load_pdf_file, filter_to_minimal_docs, text_split, download_hugging_face_embeddings
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from langchain_qdrant import QdrantVectorStore

load_dotenv()

QDRANT_URL = os.environ.get("QDRANT_URL")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY")
collection_name = "medical-chatbot"

print("=" * 50)
print("Medical Chatbot - Indexing with Qdrant")
print("=" * 50)

# 1. Initialize Qdrant Client (Cloud if credentials present, otherwise local disk)
if QDRANT_URL:
    print(f"Connecting to Qdrant Cloud: {QDRANT_URL}")
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
else:
    qdrant_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "qdrant_db")
    print(f"Using local on-disk Qdrant storage: {qdrant_path}")
    client = QdrantClient(path=qdrant_path)

# 2. Extract Data from PDF
print("Loading PDF files from data/ directory...")
extracted_data = load_pdf_file(data="data/")
print(f"Total pages loaded: {len(extracted_data)}")

filter_data = filter_to_minimal_docs(extracted_data)
text_chunks = text_split(filter_data)
print(f"Total text chunks created: {len(text_chunks)}")

# 3. Download HuggingFace Embeddings
print("Downloading / initializing Hugging Face embeddings (sentence-transformers/all-MiniLM-L6-v2)...")
embeddings = download_hugging_face_embeddings()

# 4. Create or recreate collection
if not client.collection_exists(collection_name):
    print(f"Creating collection '{collection_name}' (dim=384, metric=cosine)...")
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )
else:
    print(f"Collection '{collection_name}' already exists.")

# 5. Store documents
print("Indexing chunks into Qdrant...")
docsearch = QdrantVectorStore(
    client=client,
    collection_name=collection_name,
    embedding=embeddings,
)

batch_size = 100
for i in range(0, len(text_chunks), batch_size):
    batch = text_chunks[i : i + batch_size]
    docsearch.add_documents(batch)
    print(f"Processed chunks {i} to {min(i + batch_size, len(text_chunks))} / {len(text_chunks)}")

print("Indexing complete! Qdrant is ready to serve queries.")
if not QDRANT_URL:
    client.close()