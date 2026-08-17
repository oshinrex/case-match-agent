"""
The agent's persistent memory layer, backed by CockroachDB.

Three operations matter here:

  recall_similar_interactions  - "have I handled a case like this before?"
  write_interaction            - record what was asked, chosen, and why
  feedback_scores              - let confirmed precedents rise in future ranking

Together these close the loop: every run the agent makes becomes evidence that
improves the next one. The memory lives in the same cluster as the engagement
vectors, so retrieval and experience never disagree.
"""

import uuid
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.memory import MemoryInteraction, PrecedentFeedback


def recall_similar_interactions(
    db: Session,
    query_embedding: list[float],
    top_k: int = 3,
    max_distance: float = 0.35,
) -> list[dict[str, Any]]:
    """
    Find past runs whose query was semantically close to this one.

    Returns only genuinely close matches. `max_distance` is a cosine-distance
    cutoff: without it the agent would "recall" every unrelated case it had
    ever seen and present noise as experience.
    """

    result = db.execute(
        text("""
            SELECT
                id,
                query,
                category,
                selected_client,
                selected_industry,
                reason,
                confidence,
                created_at,
                query_embedding <=> CAST(:embedding AS VECTOR) AS distance
            FROM memory_interactions
            WHERE query_embedding IS NOT NULL
            ORDER BY distance
            LIMIT :top_k
        """),
        {
            "embedding": str(query_embedding),
            "top_k": top_k,
        },
    )

    recalled = []

    for row in result.fetchall():
        if row.distance > max_distance:
            continue

        recalled.append(
            {
                "id": str(row.id),
                "query": row.query,
                "category": row.category,
                "selected_client": row.selected_client,
                "selected_industry": row.selected_industry,
                "reason": row.reason,
                "confidence": row.confidence,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "similarity": round(1 - row.distance, 3),
            }
        )

    return recalled


def feedback_scores(db: Session) -> dict[str, int]:
    """
    Net usefulness score per engagement, from consultant feedback.

    A precedent confirmed useful three times and rejected once scores +2.
    Retrieval uses this to nudge proven precedents upward.
    """

    result = db.execute(
        text("""
            SELECT
                engagement_id,
                SUM(CASE WHEN useful THEN 1 ELSE -1 END) AS score
            FROM precedent_feedback
            GROUP BY engagement_id
        """)
    )

    return {str(row.engagement_id): int(row.score) for row in result.fetchall()}


def write_interaction(
    db: Session,
    query: str,
    query_embedding: Optional[list[float]] = None,
    category: Optional[str] = None,
    selected_engagement_id: Optional[uuid.UUID] = None,
    selected_client: Optional[str] = None,
    selected_industry: Optional[str] = None,
    reason: Optional[str] = None,
    retrieval_strategy: str = "semantic",
    search_count: int = 1,
    confidence: Optional[float] = None,
    recalled_count: int = 0,
) -> uuid.UUID:
    """
    Persist one complete agent run and return its id.

    This is the write half of agentic memory. It happens on every run, not just
    successful ones, so the record reflects what the agent actually did.
    """

    interaction = MemoryInteraction(
        query=query,
        query_embedding=query_embedding,
        category=category,
        selected_engagement_id=selected_engagement_id,
        selected_client=selected_client,
        selected_industry=selected_industry,
        reason=reason,
        retrieval_strategy=retrieval_strategy,
        search_count=search_count,
        confidence=confidence,
        recalled_count=recalled_count,
    )

    db.add(interaction)
    db.commit()
    db.refresh(interaction)

    return interaction.id


def record_feedback(
    db: Session,
    engagement_id: uuid.UUID,
    useful: bool,
    interaction_id: Optional[uuid.UUID] = None,
    client_name: Optional[str] = None,
    note: Optional[str] = None,
) -> uuid.UUID:
    """Record a consultant's verdict on a surfaced precedent."""

    feedback = PrecedentFeedback(
        interaction_id=interaction_id,
        engagement_id=engagement_id,
        client_name=client_name,
        useful=useful,
        note=note,
    )

    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    return feedback.id


def delete_feedback(db: Session, feedback_id: uuid.UUID) -> bool:
    """Retract a feedback vote, e.g. after a misclick. Returns False if it was already gone."""

    feedback = db.get(PrecedentFeedback, feedback_id)

    if feedback is None:
        return False

    db.delete(feedback)
    db.commit()

    return True


def memory_stats(db: Session) -> dict[str, Any]:
    """Summary counters for the demo UI, showing memory accumulating live."""

    interactions = db.execute(
        text("SELECT count(*) FROM memory_interactions")
    ).scalar()

    feedback_count = db.execute(
        text("SELECT count(*) FROM precedent_feedback")
    ).scalar()

    engagements = db.execute(
        text("SELECT count(*) FROM engagements WHERE embedding IS NOT NULL")
    ).scalar()

    return {
        "engagements_indexed": engagements or 0,
        "interactions_remembered": interactions or 0,
        "feedback_recorded": feedback_count or 0,
    }
