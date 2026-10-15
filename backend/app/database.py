import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session
from .config import Config

logger = logging.getLogger(__name__)

Base = declarative_base()

def get_engine():
    db_url = Config.DATABASE_URL
    try:
        # If PostgreSQL is configured, verify connection; fallback to SQLite if unreachable
        if "postgresql" in db_url:
            test_engine = create_engine(db_url, pool_pre_ping=True)
            with test_engine.connect() as conn:
                logger.info("Successfully connected to PostgreSQL / Supabase database.")
            return test_engine
        else:
            return create_engine(
                db_url,
                connect_args={"check_same_thread": False} if "sqlite" in db_url else {}
            )
    except Exception as e:
        logger.warning(f"Could not connect to configured DATABASE_URL ({e}). Falling back to local SQLite database.")
        return create_engine("sqlite:///aquasense.db", connect_args={"check_same_thread": False})

engine = get_engine()
session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
SessionLocal = scoped_session(session_factory)

def get_db():
    """Dependency helper for database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Create all tables."""
    from . import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")
