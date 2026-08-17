"""
The test that matters most for this project: memory has to compound.

Run the agent twice on related cases and assert that the second run recalls
the first out of CockroachDB. If this passes, the memory layer is doing real
work rather than decorating a search engine.
"""

from sqlalchemy.orm import Session

from app.agent.graph import case_match_agent
from app.db.database import engine
from app.services.memory import memory_stats

FIRST = """
A retail company wants to modernize its supply chain, improve inventory
visibility, and use cloud technology to optimize operations.
"""

SECOND = """
A grocery retailer needs to modernize supply chain operations and gain
better inventory visibility through cloud platforms.
"""


def show(label: str, result: dict) -> None:
    print("=" * 78)
    print(label)
    print("=" * 78)

    for step in result["trace"]:
        print(f"  [{step['step']}] {step['detail']}")

    print()


def main() -> None:
    with Session(engine) as session:
        before = memory_stats(session)

    first = case_match_agent.invoke({"query": FIRST, "category": "Retail"})
    show("RUN 1", first)

    second = case_match_agent.invoke({"query": SECOND, "category": "Retail"})
    show("RUN 2", second)

    with Session(engine) as session:
        after = memory_stats(session)

    recalled = second.get("recalled", [])

    assert recalled, "run 2 did not recall run 1 - memory is not being read"
    assert after["interactions_remembered"] == before["interactions_remembered"] + 2, (
        "both runs should have been written to memory"
    )

    print(f"Run 2 recalled {len(recalled)} prior case(s).")
    print(f"  closest: similarity {recalled[0]['similarity']} "
          f"-> {recalled[0]['selected_client']}")
    print(f"Memory grew {before['interactions_remembered']} "
          f"-> {after['interactions_remembered']} interactions.")
    print()
    print("OK - the agent read its own memory and wrote back to it.")


if __name__ == "__main__":
    main()
