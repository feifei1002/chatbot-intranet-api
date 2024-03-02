# code from https://www.squash.io/connecting-fastapi-with-postgresql-a-practical-approach/
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

app = FastAPI()

database_url = "postgresql://username:password@localhost/database_name"
engine = create_engine(database_url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
