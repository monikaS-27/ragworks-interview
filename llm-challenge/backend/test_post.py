from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class User(BaseModel):
    username: str
    password: str

@app.post("/register")
def register(user: User):
    return {"message": f"User {user.username} registered successfully!"}
