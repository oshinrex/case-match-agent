import json

import boto3

from app.config import BEDROCK_REGION, EMBEDDING_DIMENSIONS, EMBEDDING_MODEL_ID

bedrock = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION)


def generate_embedding(text: str) -> list[float]:
    """Embed text with Amazon Titan Text Embeddings V2 (1024 dimensions)."""

    response = bedrock.invoke_model(
        modelId=EMBEDDING_MODEL_ID,
        body=json.dumps(
            {
                "inputText": text,
                "dimensions": EMBEDDING_DIMENSIONS,
            }
        ),
        contentType="application/json",
        accept="application/json",
    )

    response_body = json.loads(response["body"].read())

    return response_body["embedding"]
