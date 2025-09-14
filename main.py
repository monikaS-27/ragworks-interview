# app/main.py
from fastapi import FastAPI, HTTPException, Depends, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import List
from datetime import datetime, timedelta
import os
import jwt
from passlib.context import CryptContext
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.models import Base, User, Conversation
from app.extract_text import extract_text
from app.embeddings import get_embedding
from app.vector_db import upsert_vectors, query_vectors
from app.llm import query_llm

# ===== CONFIG =====
SECRET_KEY = "mysecret"  # Change in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# ===== DATABASE =====
DATABASE_URL = "postgresql://postgres:2728@localhost:5432/llm_challenge"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

# ===== PASSWORD & AUTH =====
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# ===== APP =====
app = FastAPI(title="LLM Challenge App")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# ===== SCHEMAS =====
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    message: str
    response: str
    timestamp: datetime

# ===== HELPERS =====
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ===== ROUTES =====
@app.get("/")
def read_root():
    return {"message": "LLM Challenge app is running 🚀"}

@app.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": f"User {user.username} registered successfully!"}

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

# ===== UPLOAD DOC =====
UPLOAD_DIR = "app/static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload")
async def upload_document(file: UploadFile, current_user: User = Depends(get_current_user)):
    from fastapi import HTTPException

    try:
        # Check if file has a filename attribute
        if not hasattr(file, "filename") or not file.filename:
            raise HTTPException(status_code=400, detail="Uploaded file missing 'filename' attribute.")
        file_location = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_location, "wb") as f:
            f.write(await file.read())

        chunks = extract_text(file_location)
        vectors = []
        for i, chunk in enumerate(chunks):
            embedding = get_embedding(chunk)
            vectors.append({
                "id": f"{file.filename}_chunk_{i}",
                "values": embedding,
                "metadata": {"text": chunk}
            })
        upsert_vectors(vectors)
        return {"message": "File uploaded and indexed successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")

# ===== CHAT =====
@app.post("/chat")
def chat(chat_request: ChatRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        query_vector = get_embedding(chat_request.message)
        context_chunks = query_vectors(query_vector, top_k=3)
        context = "\n".join(context_chunks)
        prompt = f"Context:\n{context}\n\nUser: {chat_request.message}\nLLM:"
        response_text = query_llm(prompt)
        conversation = Conversation(
            user_id=current_user.id,
            query=chat_request.message,  # <-- Add this line
            message=chat_request.message,
            response=response_text
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return ChatResponse(
            message=chat_request.message,
            response=response_text,
            timestamp=conversation.timestamp
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== HISTORY =====
@app.get("/history", response_model=List[ChatResponse])
def history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    chats = db.query(Conversation).filter(Conversation.user_id == current_user.id).order_by(Conversation.timestamp).all()
    return [{"message": c.message, "response": c.response, "timestamp": c.timestamp} for c in chats]

@app.get("/favicon.ico")
async def favicon():
    return FileResponse("app/static/favicon.ico")
