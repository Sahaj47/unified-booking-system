# config.py — production-safe config for Render + PostgreSQL.
# All secrets come from environment variables. Nothing is hardcoded.

import os
from dotenv import load_dotenv

load_dotenv()   # no-op in production (Render injects env vars directly)

# ── Database ──────────────────────────────────────────────────
# Render provides DATABASE_URL as  postgres://...
# SQLAlchemy requires             postgresql://...
# The one-liner below handles both cases safely.

uri = os.getenv("DATABASE_URL")

if not uri:
    raise RuntimeError(
        "DATABASE_URL environment variable is not set. "
        "Add it in Render > Environment or your local .env file."
    )

if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

SQLALCHEMY_DATABASE_URI = uri

# ── App ───────────────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY environment variable is not set."
    )

# ── AI Insights (optional) ────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")