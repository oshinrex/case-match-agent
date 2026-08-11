from sqlalchemy.orm import Session

from app.db.database import engine
from app.models.engagements import Engagement
from app.services.embeddings import generate_embedding
from app.utils.formatter import format_engagement_for_embedding


with Session(engine) as session:
    engagements = session.query(Engagement).all()

    generated = 0
    skipped = 0

    for engagement in engagements:

        # Already embedded → skip
        if engagement.embedding is not None:
            skipped += 1
            continue

        # Convert engagement → semantic text
        text = format_engagement_for_embedding(engagement)

        # Generate 1024-dimensional Titan embedding
        embedding = generate_embedding(text)

        # Store it on the ORM object
        engagement.embedding = embedding

        generated += 1

        print(
            f"Embedded: {engagement.client_name} "
            f"({len(embedding)} dimensions)"
        )

    session.commit()

    print()
    print(f"Generated: {generated}")
    print(f"Skipped:   {skipped}")