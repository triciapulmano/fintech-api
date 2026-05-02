from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Separate database for wallet service
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@postgres-wallet:5432/fintech_wallet"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()