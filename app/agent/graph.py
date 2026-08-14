from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import END, StateGraph

from app.db.database import engine
from app.services.precedent import rank_precedents
from app.services.retrievals import search_engagements
from sqlalchemy.orm import Session


class CaseMatchState(TypedDict, total=False):
    query: str
    category: Optional[str]
    engagements: List[Any]
    result: Dict[str, Any]


def retrieve(state: CaseMatchState):
    query = state["query"]
    category = state.get("category")

    with Session(engine) as session:
        engagements = search_engagements(
            session,
            query=query,
            category=category,
            top_k=5,
        )

    return {
        "engagements": engagements
    }


def select_precedent(state: CaseMatchState):
    result = rank_precedents(
        query=state["query"],
        engagements=state["engagements"],
    )

    return {
        "result": result
    }


graph = StateGraph(CaseMatchState)

graph.add_node("retrieve", retrieve)
graph.add_node("select_precedent", select_precedent)

graph.set_entry_point("retrieve")

graph.add_edge("retrieve", "select_precedent")
graph.add_edge("select_precedent", END)

case_match_agent = graph.compile()