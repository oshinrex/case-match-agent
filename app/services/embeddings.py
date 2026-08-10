import json
import boto3


REGION = "us-east-1"
MODEL_ID = "amazon.titan-embed-text-v2:0"

bedrock = boto3.client(
    "bedrock-runtime",
    region_name=REGION
)

def generate_embedding(text: str) -> list[float]:
    response = bedrock.invoke_model(
        modelId=MODEL_ID,
        body=json.dumps({
            "inputText": text
        }),
        contentType="application/json",
        accept="application/json",
    )

    response_body = json.loads(response["body"].read())
    return response_body["embedding"]