import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.engagements import Base, Vector


class MemoryInteraction(Base):
    """
    One complete run of the Case Match agent.

    This is the agent's episodic memory: every time a consultant asks for
    precedents, the agent writes what it was asked, how it searched, what it
    chose, and how confident it was. Later runs read this back, so the system
    accumulates institutional knowledge instead of restarting cold each time.
    """

    __tablename__ = "memory_interactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # What the consultant asked
    query: Mapped[str] = mapped_column(Text, nullable=False)

    # Embedding of the query itself, so the agent can ask
    # "have I handled a case like this before?" via vector search.
    query_embedding: Mapped[Optional[list[float]]] = mapped_column(
        Vector(1024),
        nullable=True,
    )

    # Category identified for the query, if any
    category: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # The precedent the agent ultimately selected
    selected_engagement_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    selected_client: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    selected_industry: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Why the agent selected it
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # How the agent searched its memory, e.g. "semantic" or "semantic+recall"
    retrieval_strategy: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # How many search passes the agent needed before it was satisfied
    search_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Agent's confidence in the result
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # How many prior interactions the agent recalled while answering this one.
    # Zero means it was working cold; higher means it was standing on its own
    # accumulated experience.
    recalled_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )


class PrecedentFeedback(Base):
    """
    A consultant's verdict on a precedent the agent surfaced.

    This is what turns memory into learning: engagements that consultants
    confirm as useful get boosted in future retrieval, and ones they reject
    get demoted. The signal is stored in CockroachDB alongside the vectors,
    so ranking and evidence never drift apart.
    """

    __tablename__ = "precedent_feedback"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Which run this feedback came from
    interaction_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    # Which engagement was judged
    engagement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    client_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # True = useful precedent, False = not relevant
    useful: Mapped[bool] = mapped_column(Boolean, nullable=False)

    # Optional free-text note from the consultant
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
