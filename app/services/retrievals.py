from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.embeddings import generate_embedding
from typing import Optional


def search_engagements(
    db: Session,
    query: str,
    category: Optional[str] = None,
    top_k: int = 5,
):
    query_embedding = generate_embedding(query)

    # Retrieve a larger candidate pool before applying
    # category-aware ranking.
    candidate_limit = max(top_k * 4, 20)

    result = db.execute(
        text("""
            SELECT
                id,
                client_name,
                industry,
                service_line,
                business_problem,
                solution,
                outcome,
                case_narrative,
                source_url,
                embedding <=> CAST(:embedding AS VECTOR) AS distance
            FROM engagements
            WHERE embedding IS NOT NULL
            ORDER BY distance
            LIMIT :candidate_limit
        """),
        {
            "embedding": str(query_embedding),
            "candidate_limit": candidate_limit,
        },
    )

    candidates = result.fetchall()

    # If no category is provided, return pure semantic ranking.
    if not category:
        return candidates[:top_k]

    # Category-aware ranking.
    #
    # Lower distance = more semantically similar.
    # We subtract a small bonus from same-category results,
    # making them slightly more competitive without excluding
    # stronger cross-category precedents.
    category_bonus = 0.05

    ranked = sorted(
        candidates,
        key=lambda row: (
            row.distance
            - category_bonus
            if row.industry.lower() == category.lower()
            else row.distance
        )
    )

    return ranked[:top_k]