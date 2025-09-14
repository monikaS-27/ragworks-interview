# app/vector_db.py
import os
from pathlib import Path
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from fastapi import HTTPException
import pinecone

# Load .env
BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV", "us-east-1-aws")
if not PINECONE_API_KEY:
    raise RuntimeError("PINECONE_API_KEY not set in .env")

# Initialize Pinecone client
pc = Pinecone(api_key=PINECONE_API_KEY)

INDEX_NAME = "ragworks-index"
DIMENSION = 1024

# Create index if not exists
if INDEX_NAME not in [i.name for i in pc.list_indexes()]:
    pc.create_index(
        name=INDEX_NAME,
        dimension=DIMENSION,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )

# Connect to index
index = pc.Index(INDEX_NAME)

def upsert_vectors(vectors):
    """
    vectors: list of dicts like:
    {"id": "file_chunk_1", "values": [...], "metadata": {"text": "chunk text"}}
    """
    try:
        index.upsert(vectors=vectors)
    except pinecone.exceptions.PineconeApiException as e:
        raise HTTPException(status_code=400, detail=f"Pinecone upsert error: {e}")

def query_vectors(query_vector, top_k=3):
    """
    Returns a list of the top_k texts most similar to the query_vector
    """
    try:
        response = index.query(vector=query_vector, top_k=top_k, include_metadata=True)
        results = [match.metadata['text'] for match in response.matches]
        return results
    except pinecone.exceptions.PineconeApiException as e:
        raise HTTPException(status_code=400, detail=f"Pinecone query error: {e}")
