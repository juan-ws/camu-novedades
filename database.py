import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# On Railway, DATABASE_URL is set automatically when you add a PostgreSQL plugin.
# Locally it falls back to SQLite.
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./camu_payroll.db")

# SQLAlchemy requires postgresql:// not postgres:// (Railway uses the old prefix)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
