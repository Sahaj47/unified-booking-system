# config.py — works for both Render PostgreSQL and Supabase PostgreSQL

import os
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("DATABASE_URL")

if not uri:
    raise RuntimeError(
        "DATABASE_URL is not set. Add it to your .env file or hosting env vars."
    )

# Render still issues postgres:// — fix it for SQLAlchemy
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

# Supabase requires SSL. Append sslmode if not already present.
if "supabase.co" in uri and "sslmode" not in uri:
    uri += "?sslmode=require"

SQLALCHEMY_DATABASE_URI = uri

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set.")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")