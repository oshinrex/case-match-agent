"""
Case Match API.

Thin HTTP layer over the agent. The interesting behaviour all lives in
app/agent/graph.py; this module exists to expose it to the demo UI and to
accept the feedback that steers future ranking.
"""

import mimetypes
import uuid
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.agent.graph import case_match_agent
from app.db.database import engine
from app.models.engagements import Engagement
from app.services.embeddings import generate_embedding
from app.services.extraction import extract_case_fields, extract_text_from_pdf
from app.services.memory import delete_feedback, memory_stats, record_feedback
from app.utils.formatter import format_engagement_for_embedding

app = FastAPI(
    title="Case Match Agent",
    description="Agentic institutional memory for consulting precedents, "
    "backed by CockroachDB and Amazon Bedrock.",
    version="1.0.0",
)

STATIC_DIR = Path(__file__).parent / "static"

# The system mimetypes database is inconsistent across hosts - macOS knows
# .woff2, some Linux build images don't - so register it explicitly rather
# than rely on whatever happens to be installed on the deploy target.
mimetypes.add_type("font/woff2", ".woff2")


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Guarantee every error response is JSON.

    Without this, an exception that isn't already wrapped in an HTTPException
    falls through to Starlette's plain-text 500, which breaks any client that
    assumes `response.json()` always works.
    """

    return JSONResponse(status_code=500, content={"detail": f"Unexpected error: {exc}"})


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


class CaseCreate(BaseModel):
    client_name: str = Field(..., min_length=1)
    industry: str = Field(..., min_length=1)
    service_line: Optional[str] = None
    engagement_type: Optional[str] = None
    client_relationship: Optional[str] = None
    relationship_context: Optional[str] = None
    relationship_duration: Optional[str] = None
    business_problem: str = Field(..., min_length=1)
    business_capabilities: Optional[str] = None
    solution: str = Field(..., min_length=1)
    technology_stack: Optional[str] = None
    architecture_patterns: Optional[str] = None
    outcome: str = Field(..., min_length=1)
    financial_impact: Optional[str] = None
    company_size: Optional[str] = None
    project_scale: Optional[str] = None
    investment: Optional[str] = None
    case_narrative: Optional[str] = None
    source_url: Optional[str] = None


def _case_summary(engagement: Engagement) -> dict[str, Any]:
    return {
        "id": str(engagement.id),
        "client_name": engagement.client_name,
        "industry": engagement.industry,
        "service_line": engagement.service_line,
        "engagement_type": engagement.engagement_type,
        "project_scale": engagement.project_scale,
        "business_problem": engagement.business_problem,
        "created_at": engagement.created_at.isoformat() if engagement.created_at else None,
    }


def _case_detail(engagement: Engagement) -> dict[str, Any]:
    return {
        **_case_summary(engagement),
        "client_relationship": engagement.client_relationship,
        "relationship_context": engagement.relationship_context,
        "relationship_duration": engagement.relationship_duration,
        "business_capabilities": engagement.business_capabilities,
        "solution": engagement.solution,
        "technology_stack": engagement.technology_stack,
        "architecture_patterns": engagement.architecture_patterns,
        "outcome": engagement.outcome,
        "financial_impact": engagement.financial_impact,
        "company_size": engagement.company_size,
        "investment": engagement.investment,
        "case_narrative": engagement.case_narrative,
        "source_url": engagement.source_url,
    }


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


@app.post("/api/cases/extract")
def extract_case(file: UploadFile = File(...)) -> dict[str, Any]:
    """
    Read an uploaded case-study PDF and propose values for a new case.

    Nothing is saved here - this only returns a draft for the consultant to
    review, edit, and submit via POST /api/cases.
    """

    if file.content_type not in ("application/pdf", "application/x-pdf") and not (
        file.filename or ""
    ).lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a PDF file.")

    file_bytes = file.file.read()

    try:
        document_text = extract_text_from_pdf(file_bytes)
        fields = extract_case_fields(document_text)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:  # surfaced to the UI rather than a blank 500
        raise HTTPException(status_code=502, detail=f"Could not read this PDF: {exc}") from exc

    return {"fields": fields}


@app.post("/api/cases")
def create_case(request: CaseCreate) -> dict[str, Any]:
    """
    Save a reviewed case to the library and make it searchable.

    A blank case narrative is composed from the required fields, since it
    drives semantic search and should never be empty.
    """

    data = request.model_dump()

    if not data.get("case_narrative"):
        data["case_narrative"] = (
            f"{data['client_name']} ({data['industry']}): {data['business_problem']} "
            f"{data['solution']} {data['outcome']}"
        )

    for optional_text_field in (
        "business_capabilities",
        "technology_stack",
        "architecture_patterns",
    ):
        if not data.get(optional_text_field):
            data[optional_text_field] = ""

    engagement = Engagement(**data)
    embedding_text = format_engagement_for_embedding(engagement)

    try:
        engagement.embedding = generate_embedding(embedding_text)
    except Exception as exc:  # surfaced to the UI rather than a blank 500
        raise HTTPException(status_code=502, detail=f"Could not save this case: {exc}") from exc

    with Session(engine) as session:
        session.add(engagement)
        session.commit()
        session.refresh(engagement)
        result = _case_detail(engagement)

    return result


@app.get("/api/cases")
def list_cases(q: Optional[str] = None, limit: int = 20, offset: int = 0) -> dict[str, Any]:
    """Cases in the library, newest first, with optional keyword search."""

    limit = max(1, min(limit, 100))
    offset = max(0, offset)

    with Session(engine) as session:
        query = session.query(Engagement)

        if q:
            like = f"%{q}%"
            query = query.filter(
                Engagement.client_name.ilike(like)
                | Engagement.industry.ilike(like)
                | Engagement.service_line.ilike(like)
                | Engagement.business_problem.ilike(like)
            )

        total = query.with_entities(func.count(Engagement.id)).scalar() or 0

        rows = (
            query.order_by(Engagement.created_at.desc()).offset(offset).limit(limit).all()
        )

        cases = [_case_summary(row) for row in rows]

    return {"cases": cases, "total": total, "limit": limit, "offset": offset}


@app.get("/api/cases/{case_id}")
def get_case(case_id: uuid.UUID) -> dict[str, Any]:
    """Full detail for one case, for the library's expanded view."""

    with Session(engine) as session:
        engagement = session.get(Engagement, case_id)

        if engagement is None:
            raise HTTPException(status_code=404, detail="Case not found")

        return _case_detail(engagement)


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
    def landing() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/app")
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "app.html")
