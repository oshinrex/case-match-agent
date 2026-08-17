from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import certifi
from sqlalchemy import create_engine

from app.config import DATABASE_URL

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")


def _with_trust_store(url: str) -> str:
    """
    Point sslmode=verify-full at a CA bundle when no sslrootcert is set.

    Without this, psycopg2/libpq falls back to ~/.postgresql/root.crt. That
    file happens to exist on a machine that has run `cockroach cert` or
    similar, but not in a fresh container or on a judge's machine - so the
    same DATABASE_URL that works for one developer fails to connect anywhere
    else. certifi ships its own CA bundle as package data, so this resolves
    identically on macOS, Linux, and inside the container, independent of
    whatever OS trust store libpq's `sslrootcert=system` would otherwise
    depend on.
    """

    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query))

    if query.get("sslmode") == "verify-full" and "sslrootcert" not in query:
        query["sslrootcert"] = certifi.where()

    return urlunsplit(parts._replace(query=urlencode(query)))


# pool_pre_ping matters in a deployed demo: CockroachDB Cloud drops idle
# connections, and without it the first request after a quiet period fails on
# a stale socket. pool_recycle keeps connections well under that idle window.
engine = create_engine(
    _with_trust_store(DATABASE_URL),
    pool_pre_ping=True,
    pool_recycle=280,
    pool_size=5,
    max_overflow=5,
)
