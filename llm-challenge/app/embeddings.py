# from dotenv import load_dotenv
# import os

# load_dotenv()  # Load .env

# GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# if not GROQ_API_KEY:
#     raise RuntimeError("GROQ_API_KEY not set. Please export it or add it to .env")


# def get_embedding(text: str):
#     """
#     Example function to get embeddings from GROQ.
#     Replace with your actual API call logic.
#     """
#     # Pseudocode for embedding
#     # response = some_groq_library.embed(text, api_key=GROQ_API_KEY)
#     # return response['vector']
#     return [0.0] * 768  # dummy vector for testing


# app/embeddings.py
from dotenv import load_dotenv
import os

load_dotenv()  # Load .env

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY not set. Please add it to .env")

def get_embedding(text: str):
    # Dummy vector: first value is 1.0, rest are zeros
    return [1.0] + [0.0] * 1023
