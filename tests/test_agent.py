"""End-to-end run of the full agent graph, printing the reasoning trace."""

from app.agent.graph import case_match_agent

QUERY = """
A retail company wants to modernize its supply chain,
improve inventory visibility, and use cloud technology
to optimize operations.
"""


def main() -> None:
    result = case_match_agent.invoke({"query": QUERY, "category": "Retail"})

    print("=" * 78)
    print("CASE MATCH AGENT")
    print("=" * 78)
    print(QUERY.strip())

    print()
    print("REASONING TRACE")
    print("-" * 78)
    for step in result["trace"]:
        print(f"[{step['step']}] {step['detail']}")

    print()
    print("RETRIEVED PRECEDENTS")
    print("-" * 78)
    for i, e in enumerate(result["engagements"], start=1):
        print(f"{i}. {e['client_name']} ({e['industry']}) relevance {e['relevance']}")

    ranking = result["result"]
    best = result["engagements"][ranking["best_rank"] - 1]

    print()
    print("STRONGEST PRECEDENT")
    print("-" * 78)
    print(f"{best['client_name']} ({best['industry']})")
    print(ranking["reason"])

    print()
    print("RELEVANT EXPERIENCE DRAFT")
    print("-" * 78)
    print(ranking["relevant_experience"])

    print()
    print(f"Searches: {result['search_count']} "
          f"| strategy: {result['retrieval_strategy']} "
          f"| written to memory as {result['interaction_id']}")

    assert result["interaction_id"], "run was not persisted to memory"
    print()
    print("OK - full agent loop completed and persisted.")


if __name__ == "__main__":
    main()
