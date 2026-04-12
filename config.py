# ── config.py ────────────────────────────────────────────────
# Edit these before running locally

DB_CONFIG = {
    'host':     'localhost',
    'user':     'root',
    'password': 'root123',   # ← change this
    'database': 'unified_booking'
}

SECRET_KEY = 'urbs-demo-secret-key-2026'

# Optional: set your Anthropic API key for the AI Insights feature.
# Leave as empty string to use the built-in local fallback summary.
ANTHROPIC_API_KEY = ''   # e.g. 'sk-ant-...'
# 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 the credit balance is low though :/