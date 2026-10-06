"""Apify integration configuration.

All sensitive credentials are read from environment variables ONLY.
The API token is NEVER stored in the database, logs, API responses,
or anywhere outside the server process environment.
"""

import os

# Apify actor configuration
APIFY_API_TOKEN = os.environ.get("APIFY_API_TOKEN", "")
APIFY_ACTOR_ID = os.environ.get("APIFY_ACTOR_ID", "supreme_coder/linkedin-post")
APIFY_SOURCE_URL = os.environ.get(
    "APIFY_SOURCE_URL",
    "https://www.linkedin.com/school/thiagarajar-college-of-engineering/posts/",
)
APIFY_MAX_POSTS = int(os.environ.get("APIFY_MAX_POSTS", "15"))
APIFY_ENABLED = os.environ.get("APIFY_ENABLED", "true").lower() in ("1", "true", "yes")

# Apify REST API base URL
APIFY_API_BASE = "https://api.apify.com/v2"

# Timeout for Apify API calls (seconds)
APIFY_TIMEOUT = 120

# Weekly schedule: Monday 09:00 Asia/Kolkata
APIFY_SCHEDULE_CRON = "0 9 * * 1"
APIFY_SCHEDULE_TZ = "Asia/Kolkata"


def is_configured():
    """Return True if the Apify token is set and integration is enabled."""
    return bool(APIFY_ENABLED and APIFY_API_TOKEN)
