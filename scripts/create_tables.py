from app.db.database import engine
from app.models.engagements import Base

Base.metadata.create_all(engine)
print("Tables created successfully.")