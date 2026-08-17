"""
Clear the agent's episodic memory.

Useful before a demo: development runs leave near-duplicate queries behind,
and recalling your own test input is less compelling than recalling a
genuinely different prior engagement.

This never touches the engagements table - only what the agent has learned.

    python -m scripts.reset_memory          # show what would be deleted
    python -m scripts.reset_memory --yes    # actually delete
"""

import sys

from sqlalchemy import text

from app.db.database import engine


def main() -> None:
    confirmed = "--yes" in sys.argv

    with engine.connect() as connection:
        interactions = connection.execute(
            text("SELECT count(*) FROM memory_interactions")
        ).scalar()
        feedback = connection.execute(
            text("SELECT count(*) FROM precedent_feedback")
        ).scalar()

        print(f"memory_interactions: {interactions}")
        print(f"precedent_feedback:  {feedback}")

        if not confirmed:
            print()
            print("Dry run. Re-run with --yes to delete these rows.")
            return

        connection.execute(text("DELETE FROM precedent_feedback WHERE true"))
        connection.execute(text("DELETE FROM memory_interactions WHERE true"))
        connection.commit()

    print()
    print("Agent memory cleared. Engagements are untouched.")


if __name__ == "__main__":
    main()
