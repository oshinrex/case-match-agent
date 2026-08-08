import uuid 
from datetime import datetime
from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class Engagement(Base):
    __tablename__ = "engagements"

    # Identity 
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    client_name: Mapped[str] = mapped_column(String(255), nullable=False)
    industry: Mapped[str] = mapped_column(String(255), nullable=False)

    # Consulting context 
    service_line: Mapped[str] = mapped_column(String(255), nullable=True)
    engagement_type: Mapped[str] = mapped_column(String(255), nullable=True)
    client_relationship: Mapped[str] = mapped_column(String(255), nullable=True)
    relationship_context: Mapped[str] = mapped_column(String(255), nullable=True)
    relationship_duration: Mapped[str] = mapped_column(String(255), nullable=True)

    # Problem 
    business_problem: Mapped[str] = mapped_column(Text, nullable=False)
    business_capabilities: Mapped[str] = mapped_column(Text, nullable=False)

    # Solution 
    solution: Mapped[str] = mapped_column(Text, nullable=False)
    technology_stack: Mapped[str] = mapped_column(Text, nullable=False)
    architecture_patterns: Mapped[str] = mapped_column(Text, nullable=False)

    # Outcomes
    outcome: Mapped[str] = mapped_column(Text, nullable=False)
    financial_impact: Mapped[str] = mapped_column(Text, nullable=True)

    # Scale
    company_size: Mapped[str] = mapped_column(String(255), nullable=True)
    project_scale: Mapped[str] = mapped_column(String(255), nullable=True)
    investment: Mapped[str] = mapped_column(Text, nullable=True)

    # Semantic 
    case_narrative: Mapped[str] = mapped_column(Text, nullable=False)

    # Provenance
    source_url: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False)