from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import engine
from app.models.engagements import Engagement


with Session(engine) as session:

    statement = select(Engagement)

    engagements = session.scalars(statement).all()

    for engagement in engagements:
        print("=" * 60)

        print(f"Client: {engagement.client_name}")
        print(f"Industry: {engagement.industry}")

        print(f"Service Line: {engagement.service_line}")
        print(f"Engagement Type: {engagement.engagement_type}")

        print(f"Client Relationship: {engagement.client_relationship}")
        print(f"Relationship Duration: {engagement.relationship_duration}")

        print(f"Problem: {engagement.business_problem}")
        print(f"Capabilities: {engagement.business_capabilities}")

        print(f"Solution: {engagement.solution}")
        print(f"Technology Stack: {engagement.technology_stack}")
        print(f"Architecture: {engagement.architecture_patterns}")

        print(f"Outcome: {engagement.outcome}")
        print(f"Financial Impact: {engagement.financial_impact}")

        print(f"Company Size: {engagement.company_size}")
        print(f"Project Scale: {engagement.project_scale}")
        print(f"Investment: {engagement.investment}")

        print(f"Source: {engagement.source_url}")