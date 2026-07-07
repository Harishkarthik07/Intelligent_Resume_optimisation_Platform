from sqlalchemy import create_engine
from pathlib import Path
from urllib.parse import urlparse
import os
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

try:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=(settings.APP_ENV == "development"),
    )
except Exception:
    # Defer engine creation errors to init_db where we can fallback
    engine = None

SessionLocal = None
Base = declarative_base()


def get_db():
    global SessionLocal
    if SessionLocal is None:
        raise RuntimeError("Database session factory not initialized")
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"DB session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    from app.models import models  # noqa: F401 - ensure all models are imported
    global engine, SessionLocal

    # Try to initialize the configured engine first
    try:
        configured_host = urlparse(settings.DATABASE_URL).hostname
        if configured_host in {"db", "postgres"} and not os.path.exists("/.dockerenv"):
            raise RuntimeError(
                f"Database host '{configured_host}' is a Docker service name and is not resolvable in local Windows runs"
            )
        if engine is None:
            engine = create_engine(
                settings.DATABASE_URL,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
                echo=(settings.APP_ENV == "development"),
            )

        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created (primary DB).")
        return
    except Exception as e:
        logger.warning(f"Primary DB init failed: {e}")

    # Fallback to a local file-based SQLite DB for development/testing
    try:
        sqlite_dir = Path("./data")
        sqlite_dir.mkdir(parents=True, exist_ok=True)
        sqlite_path = "sqlite:///./data/dev.db"
        logger.info(f"Falling back to SQLite DB at {sqlite_path}")
        engine = create_engine(sqlite_path, connect_args={"check_same_thread": False}, echo=(settings.APP_ENV == "development"))
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created (SQLite fallback).")
    except Exception as e:
        logger.warning(f"SQLite fallback DB initialization failed — continuing without DB: {e}")
