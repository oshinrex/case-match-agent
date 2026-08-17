"""
Create the Case Match schema in CockroachDB.

Two kinds of tables are created:

  engagements          - the firm's institutional knowledge (semantic memory)
  memory_interactions  - what the agent has been asked and decided (episodic memory)
  precedent_feedback   - consultant verdicts that steer future ranking

Both engagements and memory_interactions carry a VECTOR(1024) column backed by
a CockroachDB distributed vector index, so semantic search over cases and
semantic recall over past runs stay fast as the tables grow.
"""

from sqlalchemy import text

from app.db.database import engine
from app.models.engagements import Base
import app.models.memory  # noqa: F401  - registers memory tables on Base

VECTOR_INDEXES = [
    (
        "engagements_embedding_idx",
        "CREATE VECTOR INDEX IF NOT EXISTS engagements_embedding_idx "
        "ON engagements (embedding vector_cosine_ops)",
    ),
    (
        "memory_query_embedding_idx",
        "CREATE VECTOR INDEX IF NOT EXISTS memory_query_embedding_idx "
        "ON memory_interactions (query_embedding vector_cosine_ops)",
    ),
]


def main() -> None:
    Base.metadata.create_all(engine)
    print("Tables created.")

    with engine.connect() as connection:
        for name, statement in VECTOR_INDEXES:
            connection.execute(text(statement))
            print(f"Vector index ready: {name}")

    print("Schema is ready.")


if __name__ == "__main__":
    main()
