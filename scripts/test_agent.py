from app.agent.graph import case_match_agent


query = """
A retail company wants to modernize its supply chain,
improve inventory visibility, and use cloud technology
to optimize operations.
"""

result = case_match_agent.invoke(
    {
        "query": query,
        "category": "Retail",
    }
)

print("=" * 80)
print("CASE MATCH AGENT")
print("=" * 80)

print()
print("QUERY:")
print(query)

print()
print("=" * 80)
print("RETRIEVED PRECEDENTS")
print("=" * 80)

for i, engagement in enumerate(result["engagements"], start=1):
    print()
    print(f"{i}. {engagement.client_name}")
    print(f"   Industry: {engagement.industry}")
    print(f"   Distance: {engagement.distance}")

print()
print("=" * 80)
print("BEST PRECEDENT")
print("=" * 80)

best_rank = result["result"]["best_rank"]
best = result["engagements"][best_rank - 1]

print(f"Client: {best.client_name}")
print(f"Industry: {best.industry}")

print()
print("WHY:")
print(result["result"]["reason"])

print()
print("RELEVANT EXPERIENCE:")
print(result["result"]["relevant_experience"])