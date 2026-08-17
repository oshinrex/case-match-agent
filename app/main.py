"""
Case Match API.

Thin HTTP layer over the agent. The interesting behaviour all lives in
app/agent/graph.py; this module exists to expose it to the demo UI and to
accept the feedback that steers future ranking.
"""

import uuid
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.agent.graph import case_match_agent
from app.db.database import engine
from app.services.memory import delete_feedback, memory_stats, record_feedback

app = FastAPI(
    title="Case Match Agent",
    description="Agentic institutional memory for consulting precedents, "
    "backed by CockroachDB and Amazon Bedrock.",
    version="1.0.0",
)

STATIC_DIR = Path(__file__).parent / "static"


class MatchRequest(BaseModel):
    query: str = Field(..., min_length=10, description="The new client situation.")
    category: Optional[str] = Field(
        None, description="Client industry, used as a soft ranking preference."
    )


class FeedbackRequest(BaseModel):
    engagement_id: uuid.UUID
    useful: bool
    interaction_id: Optional[uuid.UUID] = None
    client_name: Optional[str] = None
    note: Optional[str] = None


@app.get("/health")
def health() -> dict[str, Any]:
    """Liveness probe. App Runner polls this."""

    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return {"status": "ok"}


@app.get("/api/stats")
def stats() -> dict[str, Any]:
    """Counters for the UI, showing memory accumulating in real time."""

    with Session(engine) as session:
        return memory_stats(session)


@app.post("/api/match")
def match(request: MatchRequest) -> dict[str, Any]:
    """
    Run the agent against a new case.

    Declared sync on purpose: the agent makes several blocking Bedrock calls,
    so FastAPI runs it in a worker thread rather than stalling the event loop.
    """

    try:
        result = case_match_agent.invoke(
            {
                "query": request.query,
                "category": request.category,
            }
        )
    except Exception as exc:  # surfaced to the UI rather than a blank 500
        raise HTTPException(status_code=502, detail=f"Agent run failed: {exc}") from exc

    engagements = result.get("engagements", [])
    ranking = result.get("result", {})
    assessments = {a.get("rank"): a for a in ranking.get("assessments", [])}

    precedents = []

    for i, engagement in enumerate(engagements, start=1):
        assessment = assessments.get(i, {})

        precedents.append(
            {
                "rank": i,
                "id": engagement["id"],
                "client_name": engagement["client_name"],
                "industry": engagement["industry"],
                "service_line": engagement["service_line"],
                "business_problem": engagement["business_problem"],
                "solution": engagement["solution"],
                "technology_stack": engagement["technology_stack"],
                "outcome": engagement["outcome"],
                "project_scale": engagement["project_scale"],
                "relevance": engagement["relevance"],
                "similarity": engagement["similarity"],
                "boosted": engagement["boosted"],
                "same_industry": engagement["same_industry"],
                "feedback_score": engagement["feedback_score"],
                "why_relevant": assessment.get("why_relevant"),
                "key_differences": assessment.get("key_differences"),
                "is_best": i == ranking.get("best_rank"),
            }
        )

    return {
        "interaction_id": result.get("interaction_id"),
        "query": request.query,
        "precedents": precedents,
        "best_rank": ranking.get("best_rank"),
        "reason": ranking.get("reason"),
        "relevant_experience": ranking.get("relevant_experience"),
        "memory_influence": ranking.get("memory_influence"),
        "recalled": result.get("recalled", []),
        "search_count": result.get("search_count", 1),
        "retrieval_strategy": result.get("retrieval_strategy"),
        "confidence": result.get("evaluation", {}).get("confidence"),
        "trace": result.get("trace", []),
    }


@app.post("/api/feedback")
def feedback(request: FeedbackRequest) -> dict[str, Any]:
    """
    Record a consultant's verdict on a precedent.

    This is what makes the memory improve rather than merely grow: confirmed
    precedents get a ranking boost on every future search.
    """

    with Session(engine) as session:
        feedback_id = record_feedback(
            session,
            engagement_id=request.engagement_id,
            useful=request.useful,
            interaction_id=request.interaction_id,
            client_name=request.client_name,
            note=request.note,
        )

    return {"feedback_id": str(feedback_id), "recorded": True}


@app.delete("/api/feedback/{feedback_id}")
def undo_feedback(feedback_id: uuid.UUID) -> dict[str, Any]:
    """Retract a feedback vote, e.g. after a misclick."""

    with Session(engine) as session:
        removed = delete_feedback(session, feedback_id)

    if not removed:
        raise HTTPException(status_code=404, detail="Feedback not found")

    return {"feedback_id": str(feedback_id), "removed": True}


@app.get("/api/memory")
def memory(limit: int = 10) -> dict[str, Any]:
    """Recent runs, so the demo can show the memory table filling up."""

    with Session(engine) as session:
        rows = session.execute(
            text("""
                SELECT
                    id, query, category, selected_client, selected_industry,
                    confidence, search_count, retrieval_strategy,
                    recalled_count, created_at
                FROM memory_interactions
                ORDER BY created_at DESC
                LIMIT :limit
            """),
            {"limit": min(limit, 50)},
        ).fetchall()

    return {
        "interactions": [
            {
                "id": str(row.id),
                "query": row.query,
                "category": row.category,
                "selected_client": row.selected_client,
                "selected_industry": row.selected_industry,
                "confidence": row.confidence,
                "search_count": row.search_count,
                "retrieval_strategy": row.retrieval_strategy,
                "recalled_count": row.recalled_count,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ]
    }


if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")
