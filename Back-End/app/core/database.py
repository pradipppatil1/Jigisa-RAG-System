"""
SQLAlchemy database engine and session factory.

Provides the MySQL connection used by all modules that need relational
storage (e.g. routing logs, future auth tables).
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config.settings import settings

engine = create_engine(
    settings.MYSQL_DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session and closes it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables that inherit from Base (idempotent)."""
    # Import models so that Base.metadata knows about them
    import app.models.routing_log  # noqa: F401
    import app.models.guardrail_log  # noqa: F401
    import app.models.user  # noqa: F401
    import app.models.chat_history  # noqa: F401
    import app.models.refresh_token # noqa: F401
    Base.metadata.create_all(bind=engine)

