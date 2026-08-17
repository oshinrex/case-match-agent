from sqlalchemy import create_engine

from app.config import DATABASE_URL

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

# pool_pre_ping matters in a deployed demo: CockroachDB Cloud drops idle
# connections, and without it the first request after a quiet period fails on
# a stale socket. pool_recycle keeps connections well under that idle window.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=280,
    pool_size=5,
    max_overflow=5,
)
