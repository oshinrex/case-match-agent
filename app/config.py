"""
Central configuration.

Bedrock region is kept separate from AWS_REGION on purpose: model access is
granted per region, and the cluster or the deployment may well live somewhere
the models are not enabled. Pinning BEDROCK_REGION avoids a silent switch to a
region where Titan or Nova is not available.
"""

import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

BEDROCK_REGION = os.getenv("BEDROCK_REGION", "us-east-1")
EMBEDDING_MODEL_ID = os.getenv("EMBEDDING_MODEL_ID", "amazon.titan-embed-text-v2:0")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0")

EMBEDDING_DIMENSIONS = 1024
