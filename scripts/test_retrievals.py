from sqlalchemy.orm import Session

from app.db.database import engine
from app.services.retrievals import search_engagements


query = """
A retail company wants to modernize its supply chain,
improve inventory visibility, and use cloud technology
to optimize operations.
"""

with Session(engine) as session:
    engagements = search_engagements(
        session,
        query,
        category="Retail",
        top_k=5,
    )

    for engagement in engagements:
        print("=" * 80)
        print(f"Client: {engagement.client_name}")
        print(f"Industry: {engagement.industry}")
        print(f"Distance: {engagement.distance}")
        print(f"Problem: {engagement.business_problem}")
        print(f"Solution: {engagement.solution}")