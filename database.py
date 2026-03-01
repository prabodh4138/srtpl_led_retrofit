import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ---------------------------------------
# DATABASE URL (From Streamlit Secrets)
# ---------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL not set")

# ---------------------------------------
# ENGINE CONFIG (Pooler Safe)
# ---------------------------------------
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=5,
    pool_recycle=300
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)
