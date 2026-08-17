"""
Semantic retrieval over the firm's engagement memory.

Ranking blends three signals, in descending order of influence:

  1. Cosine distance between the case and each engagement (the real work)
  2. A small same-industry bonus, so industry helps but never gates
  3. A small bonus for precedents consultants have confirmed useful

Signals 2 and 3 are deliberately small. The point of the product is finding
structurally similar work across industries, so nothing is allowed to
overwhelm semantic similarity.
"""

from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.embeddings import generate_embedding
from app.services.memory import feedback_scores

CATEGORY_BONUS = 0.05
FEEDBACK_BONUS_PER_VOTE = 0.02
MAX_FEEDBACK_BONUS = 0.06

SELECT_COLUMNS = """
    id,
    client_name,
    industry,
    service_line,
    engagement_type,
    business_problem,
    business_capabilities,
    solution,
    technology_stack,
    architecture_patterns,
    outcome,
    financial_impact,
    company_size,
    project_scale,
    case_narrative,
    source_url
"""


def search_engagements(
    db: Session,
    query: Optional[str] = None,
    category: Optional[str] = None,
    top_k: int = 5,
    query_embedding: Optional[list[float]] = None,
    use_feedback: bool = True,
    exclude_ids: Optional[list[str]] = None,
) -> list[dict[str, Any]]:
    """
    Return the top_k most structurally similar past engagements.

    Pass `query_embedding` when the caller already has one - the agent embeds
    the case once and reuses it for both memory recall and this search, which
    halves the Bedrock calls per run.
    """

    if query_embedding is None:
        if not query:
            raise ValueError("search_engagements needs either query or query_embedding")
        query_embedding = generate_embedding(query)

    # Pull a wider candidate pool than we need, so the bonuses below have
    # something to reorder. Ranking on an already-truncated list would make
    # them almost inert.
    candidate_limit = max(top_k * 4, 20)

    result = db.execute(
        text(f"""
            SELECT
                {SELECT_COLUMNS},
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

    scores = feedback_scores(db) if use_feedback else {}
    excluded = set(exclude_ids or [])

    candidates = []

    for row in result.fetchall():
        engagement_id = str(row.id)

        if engagement_id in excluded:
            continue

        distance = float(row.distance)
        adjusted = distance

        same_industry = bool(
            category and row.industry and row.industry.lower() == category.lower()
        )

        if same_industry:
            adjusted -= CATEGORY_BONUS

        # Lower adjusted score = better, so a positive feedback score
        # subtracts distance and a negative one adds it.
        vote = scores.get(engagement_id, 0)
        feedback_bonus = max(
            -MAX_FEEDBACK_BONUS,
            min(MAX_FEEDBACK_BONUS, vote * FEEDBACK_BONUS_PER_VOTE),
        )
        adjusted -= feedback_bonus

        candidates.append(
            {
                "id": engagement_id,
                "client_name": row.client_name,
                "industry": row.industry,
                "service_line": row.service_line,
                "engagement_type": row.engagement_type,
                "business_problem": row.business_problem,
                "business_capabilities": row.business_capabilities,
                "solution": row.solution,
                "technology_stack": row.technology_stack,
                "architecture_patterns": row.architecture_patterns,
                "outcome": row.outcome,
                "financial_impact": row.financial_impact,
                "company_size": row.company_size,
                "project_scale": row.project_scale,
                "case_narrative": row.case_narrative,
                "source_url": row.source_url,
                "distance": round(distance, 4),
                # Raw semantic closeness, before any bonuses.
                "similarity": round(max(0.0, 1 - distance), 3),
                # What the list is actually ordered by. Shown as the headline
                # number so the ranking never looks out of order in the UI.
                "relevance": round(max(0.0, min(1.0, 1 - adjusted)), 3),
                "boosted": bool(same_industry or vote),
                "same_industry": same_industry,
                "feedback_score": vote,
                "_rank_score": adjusted,
            }
        )

    candidates.sort(key=lambda c: c["_rank_score"])

    return candidates[:top_k]
