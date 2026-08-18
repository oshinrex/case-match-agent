"""
Reasoning over retrieved precedents.

Retrieval finds engagements that are numerically close. These functions decide
whether those candidates are actually good enough, and turn the winner into
language a consultant can put in a pitch.
"""

import json
from typing import Any, Optional

from app.services.bedrock import invoke_json


def _summarize_candidates(engagements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Trim engagements down to the fields the model needs to judge them."""

    return [
        {
            "rank": i,
            "client_name": e["client_name"],
            "industry": e["industry"],
            "business_problem": e["business_problem"],
            "solution": e["solution"],
            "technology_stack": e.get("technology_stack"),
            "architecture_patterns": e.get("architecture_patterns"),
            "outcome": e["outcome"],
            "project_scale": e.get("project_scale"),
            "relevance": e.get("relevance"),
        }
        for i, e in enumerate(engagements, start=1)
    ]


def _format_recalled(recalled: Optional[list[dict[str, Any]]]) -> str:
    """Render prior runs as context the model can lean on."""

    if not recalled:
        return "This is the first time the firm has been asked about a case like this."

    lines = []

    for r in recalled:
        lines.append(
            f"- Previously asked: \"{(r['query'] or '').strip()[:200]}\" "
            f"(similarity {r.get('similarity')}). "
            f"The firm went with {r.get('selected_client')} "
            f"({r.get('selected_industry')}). Reason: {r.get('reason')}"
        )

    return "\n".join(lines)


def evaluate_precedents(
    query: str,
    engagements: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Judge whether the current candidate set is strong enough to answer with.

    This is the decision that makes the graph agentic: a weak verdict sends the
    agent back to search again rather than answering with what it has.
    """

    prompt = f"""You are evaluating whether a consulting precedent search has
produced enough strong candidates.

Current consulting problem:

{query}

Retrieved engagements:

{json.dumps(_summarize_candidates(engagements), indent=2)}

Determine whether these results contain enough strong precedents.

A result is strong when it has meaningful similarity in:
- business problem
- solution approach
- desired outcome

Industry similarity is useful but must NOT be required. A different industry
with the same underlying transformation pattern is a strong precedent.

Return ONLY valid JSON:

{{
    "good_enough": true,
    "confidence": 0.85,
    "reason": "Explain whether the current candidates are sufficient.",
    "missing": "What kind of engagement would strengthen this set, if any."
}}

Set good_enough to false if the candidates are weak, generic, or
insufficiently relevant."""

    return invoke_json(prompt, max_tokens=400, temperature=0.1)


def rank_precedents(
    query: str,
    engagements: list[dict[str, Any]],
    recalled: Optional[list[dict[str, Any]]] = None,
) -> dict[str, Any]:
    """
    Pick the strongest precedent and draft the pitch language for it.

    `recalled` carries what the agent decided on similar cases in the past.
    It is advisory, not binding - past choices inform the reasoning but a
    better candidate in the current set should still win.
    """

    prompt = f"""You are a consulting precedent-selection agent.

A consultant is working on this problem:

{query}

Below are historical consulting engagements retrieved by semantic similarity
from the firm's institutional memory:

{json.dumps(_summarize_candidates(engagements), indent=2)}

What the firm has done on similar requests before:

{_format_recalled(recalled)}

Evaluate each candidate on:
1. Similarity of the underlying business problem
2. Similarity of the solution approach and architecture
3. Transferability across industries
4. Relevance of the outcome
5. Overall usefulness as a consulting precedent

Prior firm decisions are useful context, but choose the best precedent for
THIS case even if it differs from what was chosen before.

Return ONLY valid JSON in this exact shape:

{{
    "best_rank": 1,
    "reason": "Why this engagement is the strongest precedent for this case.",
    "relevant_experience": "A polished paragraph, in consulting pitch voice, describing this relevant experience. Write it so it could be pasted into a proposal.",
    "assessments": [
        {{
            "rank": 1,
            "why_relevant": "One or two sentences on what makes this engagement applicable.",
            "key_differences": "What does not transfer, stated honestly."
        }}
    ],
    "memory_influence": "One sentence on whether prior firm decisions informed this choice, or 'No prior similar cases.' if there were none."
}}

Include one entry in "assessments" for every candidate, in rank order."""

    return invoke_json(prompt, max_tokens=2000, temperature=0.2)
