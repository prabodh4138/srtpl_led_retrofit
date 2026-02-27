import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# -----------------------------------
# DATABASE URL LOGIC
# -----------------------------------

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Render PostgreSQL
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True
    )
else:
    # Local SQLite
    engine = create_engine(
        "sqlite:///srtpl.db",
        connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)