from sqlalchemy.orm import Session

from app.db.database import engine
from app.services.retrievals import search_engagements
from app.services.precedent import rank_precedents


query = """
A retail company wants to modernize its supply chain,
improve inventory visibility, and use cloud technology
to optimize operations.
"""


with Session(engine) as session:

    # Step 1: Retrieve candidate precedents
    engagements = search_engagements(
        session,
        query,
        category="Retail",
        top_k=5,
    )

    print("=" * 80)
    print("QUERY")
    print("=" * 80)
    print(query)

    print()
    print("=" * 80)
    print("TOP PRECEDENTS")
    print("=" * 80)

    for i, engagement in enumerate(engagements, start=1):
        print()
        print(f"{i}. {engagement.client_name}")
        print(f"   Industry: {engagement.industry}")
        print(f"   Distance: {engagement.distance}")
        print(f"   Problem: {engagement.business_problem}")
        print(f"   Solution: {engagement.solution}")

    # Step 2: Ask the precedent agent to select the strongest case
    result = rank_precedents(
        query=query,
        engagements=engagements,
    )

    print()
    print("=" * 80)
    print("BEST PRECEDENT")
    print("=" * 80)

    best_rank = result["best_rank"]

    if 1 <= best_rank <= len(engagements):
        best = engagements[best_rank - 1]

        print(f"Client: {best.client_name}")
        print(f"Industry: {best.industry}")

    print()
    print("WHY:")
    print(result["reason"])

    print()
    print("RELEVANT EXPERIENCE:")
    print(result["relevant_experience"])

    