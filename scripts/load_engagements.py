import json
from pathlib import Path
from sqlalchemy.orm import Session
from app.db.database import engine
from app.models.engagements import Engagement

DATA_FILE = Path("data/engagements.json")

with open(DATA_FILE, "r") as f:
    engagements_data = json.load(f)

with Session(engine) as session:
    added = 0
    skipped = 0

    for data in engagements_data:
        # Prevent duplicate clients from being inserted
        existing = (
            session.query(Engagement)
            .filter_by(client_name=data["client_name"])
            .first()
        )

        if existing:
            skipped += 1
            continue

        engagement = Engagement(**data)
        session.add(engagement)
        added += 1

    session.commit()

print(f"Added:   {added}")
print(f"Skipped: {skipped}")