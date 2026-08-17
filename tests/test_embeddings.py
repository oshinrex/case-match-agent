from app.services.embeddings import generate_embedding


text = """
A manufacturing company needed a real-time analytics platform
to improve supply chain visibility and operational decision-making.
"""

embedding = generate_embedding(text)

print("Embedding generated!")
print("Dimensions:", len(embedding))
print("First 5 values:", embedding[:5])