from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message": "LLM Challenge app is running 🚀"}



