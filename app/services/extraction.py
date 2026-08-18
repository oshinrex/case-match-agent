"""
Turn an uploaded case-study document into a draft case record.

Extraction only ever produces a draft: nothing reaches the database until a
person reviews the fields and submits them through the normal case-creation
endpoint.
"""

import io
from typing import Any, Optional

from pypdf import PdfReader

from app.services.bedrock import invoke_json

MAX_CHARS = 20000

CASE_FIELDS = [
    "client_name",
    "industry",
    "service_line",
    "engagement_type",
    "client_relationship",
    "relationship_context",
    "relationship_duration",
    "business_problem",
    "business_capabilities",
    "solution",
    "technology_stack",
    "architecture_patterns",
    "outcome",
    "financial_impact",
    "company_size",
    "project_scale",
    "investment",
    "case_narrative",
    "source_url",
]


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Pull raw text out of a PDF, trimmed to a size the model can read in one pass."""

    reader = PdfReader(io.BytesIO(file_bytes))
    pages = [page.extract_text() or "" for page in reader.pages]
    document_text = "\n\n".join(pages).strip()

    if not document_text:
        raise ValueError(
            "No readable text found in this PDF. It may be a scanned image "
            "rather than a text document."
        )

    return document_text[:MAX_CHARS]


def extract_case_fields(document_text: str) -> dict[str, Optional[Any]]:
    """Ask the model to read a case study and propose values for a new case record."""

    prompt = f"""You are helping a consulting firm add a past engagement to its
case library. Read the case study document below and extract structured
fields describing the engagement.

Document:

{document_text}

Return ONLY valid JSON with exactly these keys. Use null for any field the
document does not clearly support - never invent information.

{{
    "client_name": "Organization the work was done for",
    "industry": "Client's industry",
    "service_line": "Type of consulting service delivered",
    "engagement_type": "Short label for the kind of engagement",
    "client_relationship": "Nature of the firm's relationship with the client",
    "relationship_context": "One sentence of context on the relationship",
    "relationship_duration": "How long the firm has worked with this client",
    "business_problem": "The problem the client faced, in 1-3 sentences",
    "business_capabilities": "Comma-separated business capabilities involved",
    "solution": "What was built or delivered, in 1-3 sentences",
    "technology_stack": "Comma-separated technologies used",
    "architecture_patterns": "Comma-separated architecture patterns used",
    "outcome": "The measurable or qualitative result, in 1-3 sentences",
    "financial_impact": "Financial or business impact, if stated",
    "company_size": "Size of the client organization, if stated",
    "project_scale": "Scale or scope of the project",
    "investment": "Investment or budget figures, if stated",
    "case_narrative": "A 3-5 sentence narrative summarizing the whole engagement, written so it is easy to match against future situations",
    "source_url": "A URL for this case if one appears in the document, else null"
}}"""

    data = invoke_json(prompt, max_tokens=1800, temperature=0.1)

    return {field: data.get(field) for field in CASE_FIELDS}
