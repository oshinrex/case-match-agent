"""
The Case Match agent.

    embed -> recall -> retrieve -> evaluate -+-> select -> remember -> END
                          ^                  |
                          +--- broaden <-----+

Two things make this agentic rather than a fixed RAG chain:

  - `evaluate` can reject its own results and send the agent back to search
    again with a different strategy, instead of answering with weak matches.
  - `recall` and `remember` mean the agent starts each run with what it learned
    from previous ones, and leaves the run better off than it found it.

Both the engagement vectors and the memory of past runs live in CockroachDB.
"""

import uuid
from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import END, StateGraph
from sqlalchemy.orm import Session

from app.db.database import engine
from app.services.embeddings import generate_embedding
from app.services.memory import (
    recall_similar_interactions,
    write_interaction,
)
from app.services.precedent import evaluate_precedents, rank_precedents
from app.services.retrievals import search_engagements

MAX_SEARCHES = 2
INITIAL_TOP_K = 5
BROADENED_TOP_K = 8


class CaseMatchState(TypedDict, total=False):
    query: str
    category: Optional[str]
    query_embedding: List[float]
    recalled: List[Dict[str, Any]]
    engagements: List[Dict[str, Any]]
    evaluation: Dict[str, Any]
    result: Dict[str, Any]
    search_count: int
    retrieval_strategy: str
    interaction_id: Optional[str]
    trace: List[Dict[str, Any]]


def _step(state: CaseMatchState, name: str, detail: str) -> List[Dict[str, Any]]:
    """Append a human-readable step to the trace shown in the demo UI."""

    return state.get("trace", []) + [{"step": name, "detail": detail}]


def embed_case(state: CaseMatchState) -> Dict[str, Any]:
    """
    Embed the incoming case once.

    The same vector is reused for memory recall and engagement search, so a run
    costs one Bedrock embedding call rather than one per lookup.
    """

    embedding = generate_embedding(state["query"])

    return {
        "query_embedding": embedding,
        "trace": _step(
            state,
            "embed",
            f"Embedded the case with Amazon Titan V2 ({len(embedding)} dimensions).",
        ),
    }


def recall(state: CaseMatchState) -> Dict[str, Any]:
    """Ask CockroachDB whether the firm has handled a case like this before."""

    with Session(engine) as session:
        recalled = recall_similar_interactions(
            session,
            query_embedding=state["query_embedding"],
            top_k=3,
        )

    if recalled:
        detail = (
            f"Recalled {len(recalled)} similar case(s) from memory. "
            f"Closest: \"{recalled[0]['query'].strip()[:80]}\" "
            f"(similarity {recalled[0]['similarity']}), "
            f"where the firm chose {recalled[0]['selected_client']}."
        )
    else:
        detail = "No similar prior cases in memory. Working from engagements alone."

    return {
        "recalled": recalled,
        "trace": _step(state, "recall", detail),
    }


def retrieve(state: CaseMatchState) -> Dict[str, Any]:
    """First pass: semantic search with a light same-industry preference."""

    with Session(engine) as session:
        engagements = search_engagements(
            session,
            query_embedding=state["query_embedding"],
            category=state.get("category"),
            top_k=INITIAL_TOP_K,
        )

    return {
        "engagements": engagements,
        "search_count": 1,
        "retrieval_strategy": "semantic",
        "trace": _step(
            state,
            "retrieve",
            f"Vector search over engagements returned {len(engagements)} candidates.",
        ),
    }


def evaluate(state: CaseMatchState) -> Dict[str, Any]:
    """Judge the candidate set, and decide whether it is worth answering with."""

    evaluation = evaluate_precedents(
        query=state["query"],
        engagements=state["engagements"],
    )

    verdict = "strong enough" if evaluation.get("good_enough") else "too weak"

    return {
        "evaluation": evaluation,
        "trace": _step(
            state,
            "evaluate",
            f"Judged the candidate set {verdict} "
            f"(confidence {evaluation.get('confidence')}). "
            f"{evaluation.get('reason', '')}",
        ),
    }


def decide_next_step(state: CaseMatchState) -> str:
    evaluation = state.get("evaluation", {})

    if evaluation.get("good_enough"):
        return "select_precedent"

    if state.get("search_count", 0) >= MAX_SEARCHES:
        return "select_precedent"

    return "broaden_search"


def broaden_search(state: CaseMatchState) -> Dict[str, Any]:
    """
    Second pass, deliberately different from the first.

    The industry preference is dropped entirely and the net is widened. If the
    first search was too anchored on the client's own sector, this is what
    surfaces the structurally similar work from somewhere else - which is the
    whole premise of the product.
    """

    with Session(engine) as session:
        engagements = search_engagements(
            session,
            query_embedding=state["query_embedding"],
            category=None,
            top_k=BROADENED_TOP_K,
        )

    return {
        "engagements": engagements,
        "search_count": state.get("search_count", 0) + 1,
        "retrieval_strategy": "semantic+cross-industry",
        "trace": _step(
            state,
            "broaden",
            "First set was weak, so the agent dropped the industry preference "
            f"and searched cross-industry, returning {len(engagements)} candidates.",
        ),
    }


def select_precedent(state: CaseMatchState) -> Dict[str, Any]:
    """Choose the strongest precedent and draft the pitch language."""

    result = rank_precedents(
        query=state["query"],
        engagements=state["engagements"],
        recalled=state.get("recalled"),
    )

    best_rank = result.get("best_rank", 1)
    engagements = state["engagements"]

    # Ranks are 1-based and model-supplied, so clamp before indexing.
    if not isinstance(best_rank, int) or not 1 <= best_rank <= len(engagements):
        best_rank = 1
        result["best_rank"] = 1

    best = engagements[best_rank - 1]

    return {
        "result": result,
        "trace": _step(
            state,
            "select",
            f"Selected {best['client_name']} ({best['industry']}) "
            "as the strongest precedent.",
        ),
    }


def remember(state: CaseMatchState) -> Dict[str, Any]:
    """
    Write the run back to CockroachDB.

    This is the half that compounds: the next consultant to ask something
    similar will have this decision recalled for them.
    """

    engagements = state["engagements"]
    result = state.get("result", {})
    best = engagements[result.get("best_rank", 1) - 1] if engagements else None

    with Session(engine) as session:
        interaction_id = write_interaction(
            session,
            query=state["query"],
            query_embedding=state["query_embedding"],
            category=state.get("category"),
            selected_engagement_id=uuid.UUID(best["id"]) if best else None,
            selected_client=best["client_name"] if best else None,
            selected_industry=best["industry"] if best else None,
            reason=result.get("reason"),
            retrieval_strategy=state.get("retrieval_strategy", "semantic"),
            search_count=state.get("search_count", 1),
            confidence=state.get("evaluation", {}).get("confidence"),
            recalled_count=len(state.get("recalled", [])),
        )

    return {
        "interaction_id": str(interaction_id),
        "trace": _step(
            state,
            "remember",
            "Wrote this run to CockroachDB. The firm's memory now includes it.",
        ),
    }


graph = StateGraph(CaseMatchState)

graph.add_node("embed_case", embed_case)
graph.add_node("recall", recall)
graph.add_node("retrieve", retrieve)
graph.add_node("evaluate", evaluate)
graph.add_node("broaden_search", broaden_search)
graph.add_node("select_precedent", select_precedent)
graph.add_node("remember", remember)

graph.set_entry_point("embed_case")

graph.add_edge("embed_case", "recall")
graph.add_edge("recall", "retrieve")
graph.add_edge("retrieve", "evaluate")

graph.add_conditional_edges(
    "evaluate",
    decide_next_step,
    {
        "select_precedent": "select_precedent",
        "broaden_search": "broaden_search",
    },
)

graph.add_edge("broaden_search", "evaluate")
graph.add_edge("select_precedent", "remember")
graph.add_edge("remember", END)

case_match_agent = graph.compile()
