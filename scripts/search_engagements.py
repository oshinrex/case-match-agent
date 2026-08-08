from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import engine
from app.models.engagements import Engagement


with Session(engine) as session:

    statement = select(Engagement).where(
        Engagement.architecture_patterns.contains(
            "Event-driven architecture"
        )
    )

    engagements = session.scalars(statement).all()

    print(f"Found {len(engagements)} matching engagements.")

    for engagement in engagements:
        print(
            f"{engagement.client_name} "
            f"— {engagement.industry}"
        )