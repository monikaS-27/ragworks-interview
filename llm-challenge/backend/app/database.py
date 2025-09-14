from sqlmodel import SQLModel, create_engine, Session

DATABASE_URL = "postgresql://interview_user:interview_password@localhost:5432/llm_challenge"


engine = create_engine(DATABASE_URL, echo=True)  # echo=True shows SQL logs

# Dependency to get DB session
def get_session():
    with Session(engine) as session:
        yield session

