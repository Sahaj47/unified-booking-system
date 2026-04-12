# ── db.py ─────────────────────────────────────────────────────
# Single helper to create a fresh MySQL connection per request.

import mysql.connector
from config import DB_CONFIG

def get_connection():
    """Return a new MySQL connection using settings from config.py."""
    return mysql.connector.connect(**DB_CONFIG)