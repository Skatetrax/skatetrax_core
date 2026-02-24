from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

_engine = None
_SessionFactory = None


def get_engine():
    global _engine
    if _engine is None:
        db_url = os.environ.get('PGDB_HOST')
        db_name = os.environ.get('PGDB_NAME')
        db_user = os.environ.get('PGDB_USER')
        passwd = os.environ.get('PGDB_PASSWORD')
        _engine = create_engine(f'postgresql://{db_user}:{passwd}@{db_url}/{db_name}')
    return _engine


def get_session_factory():
    global _SessionFactory
    if _SessionFactory is None:
        _SessionFactory = sessionmaker(bind=get_engine())
    return _SessionFactory


def create_session():
    """Create a new session instance on demand."""
    return get_session_factory()()


def check_db_health():
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"DB health check failed: {e}")
        return False


def __getattr__(name):
    """Backward-compatible lazy access for st_bea imports of Session and engine."""
    if name == "engine":
        return get_engine()
    if name == "Session":
        return get_session_factory()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
