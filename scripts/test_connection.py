from sqlalchemy import text
from app.db.database import engine

with engine.connect() as connection:
    result = connection.execute(text("SELECT now()"))
    print(result.fetchone())