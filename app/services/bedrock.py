"""Shared Bedrock chat-model client, used anywhere we need a JSON reply."""

import json

import boto3

from app.config import BEDROCK_MODEL_ID as MODEL_ID
from app.config import BEDROCK_REGION

bedrock = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION)


def invoke_json(prompt: str, max_tokens: int = 1200, temperature: float = 0.2) -> dict:
    """
    Call Bedrock and parse a JSON object out of the reply.

    Models wrap JSON in markdown fences often enough that stripping them is
    not optional; we also fall back to slicing between the outermost braces
    so one stray sentence of preamble cannot break a live demo.
    """

    response = bedrock.invoke_model(
        modelId=MODEL_ID,
        body=json.dumps(
            {
                "messages": [{"role": "user", "content": [{"text": prompt}]}],
                "inferenceConfig": {
                    "maxTokens": max_tokens,
                    "temperature": temperature,
                },
            }
        ),
        contentType="application/json",
        accept="application/json",
    )

    body = json.loads(response["body"].read())
    text = body["output"]["message"]["content"][0]["text"].strip()

    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        text = text.removeprefix("json").strip()

    if text.endswith("```"):
        text = text[: -3].strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")

        if start == -1 or end == -1:
            raise

        return json.loads(text[start : end + 1])
