"""Smoke test: retrieval feeds reasoning, and reasoning picks a defensible winner."""

from sqlalchemy.orm import Session

from app.db.database import engine
from app.services.precedent import rank_precedents
from app.services.retrievals import search_engagements

QUERY = """
A retail company wants to modernize its supply chain,
improve inventory visibility, and use cloud technology
to optimize operations.
"""


def main() -> None:
    with Session(engine) as session:
        engagements = search_engagements(
            session,
            query=QUERY,
            category="Retail",
            top_k=5,
        )

    assert engagements, "retrieval returned nothing"

    result = rank_precedents(query=QUERY, engagements=engagements)

    best_rank = result["best_rank"]
    assert 1 <= best_rank <= len(engagements), f"best_rank {best_rank} out of range"

    best = engagements[best_rank - 1]

    print("=" * 78)
    print("TOP PRECEDENTS")
    print("=" * 78)

    for i, e in enumerate(engagements, start=1):
        marker = " <- strongest" if i == best_rank else ""
        print(f"{i}. {e['client_name']} ({e['industry']}) "
              f"relevance {e['relevance']}{marker}")

    print()
    print("=" * 78)
    print(f"STRONGEST: {best['client_name']}")
    print("=" * 78)
    print(result["reason"])
    print()
    print("RELEVANT EXPERIENCE DRAFT")
    print("-" * 78)
    print(result["relevant_experience"])
    print()
    print("OK - reasoning produced a ranked selection and pitch language.")


if __name__ == "__main__":
    main()
