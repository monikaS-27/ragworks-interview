from app.database import engine
from app.models import User, Conversation
from sqlmodel import SQLModel

print("Creating tables...")
SQLModel.metadata.create_all(engine)
print("✅ Tables created successfully!")
