"""Smoke test: vector retrieval returns ranked, structurally relevant cases."""

from sqlalchemy.orm import Session

from app.db.database import engine
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

    scores = [e["relevance"] for e in engagements]
    assert scores == sorted(scores, reverse=True), "results are not in ranked order"

    for i, e in enumerate(engagements, start=1):
        print("=" * 78)
        print(f"{i}. {e['client_name']} ({e['industry']})")
        print(f"   relevance {e['relevance']}  |  raw similarity {e['similarity']}")
        print(f"   problem:  {e['business_problem']}")
        print(f"   solution: {e['solution']}")

    print()
    print(f"OK - {len(engagements)} precedents, correctly ordered.")


if __name__ == "__main__":
    main()
