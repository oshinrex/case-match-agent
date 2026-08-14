import json
from typing import Any

import boto3


REGION = "us-east-1"
MODEL_ID = "amazon.nova-lite-v1:0"

bedrock = boto3.client("bedrock-runtime", region_name=REGION)

def rank_precedents(query: str, engagements: list[Any]):
    candidates = []

    for i, engagement in enumerate(engagements, start=1):
        candidates.append(
            {
                "rank": i,
                "client_name": engagement.client_name,
                "industry": engagement.industry,
                "business_problem": engagement.business_problem,
                "solution": engagement.solution,
                "outcome": engagement.outcome,
            }
        )

    prompt = f"""You are a consulting precedent-selection agent.
    A consultant is working on this problem:
    {query}

    Below are historical consulting engagements retrieved by semantic similarity:

    {json.dumps(candidates, indent=2)}

    Determine which engagement is the strongest precedent for the consultant's
    current problem.

    Evaluate:
    1. Similarity of the business problem
    2. Similarity of the solution approach
    3. Transferability across industries
    4. Relevance of the outcome
    5. Overall usefulness as consulting precedent

    Return ONLY valid JSON in this format:

    {{
        "best_rank": 1,
        "reason": "Why this engagement is the strongest precedent",
        "relevant_experience": "A concise consulting-style summary of the relevant experience"
    }}
    """

    response = bedrock.invoke_model(
        modelId=MODEL_ID,
        body=json.dumps(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ],
                "inferenceConfig": {
                    "maxTokens": 500,
                    "temperature": 0.2,
                },
            }
        ),
        contentType="application/json",
        accept="application/json",
    )

    response_body = json.loads(response["body"].read())
    text = response_body["output"]["message"]["content"][0]["text"]

    text = text.strip()

    if text.startswith("```json"):
        text = text[len("```json"):]

    if text.endswith("```"):
        text = text[:-3]

    text = text.strip()
    return json.loads(text)