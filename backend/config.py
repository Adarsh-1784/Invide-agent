"""
EcoNITH Configuration - Environment variable management
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# === AWS Configuration ===
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "amazon.nova-pro-v1:0")

# === Application Mode ===
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

# === Database ===
DATABASE_PATH = Path(__file__).parent / "econith.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATABASE_PATH}")

# === Paths ===
BACKEND_DIR = Path(__file__).parent
STATIC_DIR = BACKEND_DIR / "static"
UPLOADS_DIR = STATIC_DIR / "uploads"
CHARTS_DIR = STATIC_DIR / "charts"
MAPS_DIR = STATIC_DIR / "maps"

# Create directories
for d in [STATIC_DIR, UPLOADS_DIR, CHARTS_DIR, MAPS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# === Server ===
BACKEND_HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# === NIT Hamirpur Campus Data ===
CAMPUS_CENTER_LAT = 31.7082
CAMPUS_CENTER_LNG = 76.5274
CAMPUS_NAME = "National Institute of Technology, Hamirpur"
CAMPUS_SHORT = "NIT Hamirpur"


def is_aws_configured() -> bool:
    """Check if AWS credentials are properly configured."""
    return bool(AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY)


def get_bedrock_client():
    """Get Bedrock runtime client, returns None if not configured."""
    if not is_aws_configured():
        return None
    try:
        import boto3
        return boto3.client(
            "bedrock-runtime",
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        )
    except Exception as e:
        print(f"[WARN] Failed to create Bedrock client: {e}")
        return None
