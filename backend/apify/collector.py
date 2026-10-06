"""Apify LinkedIn post collector.

Fetches posts from the Apify `supreme_coder/linkedin-post` actor and
returns them as plain dicts.  This module is ONLY responsible for
fetching; it never writes to any database.

Security:
  * The API token is read from the environment and NEVER logged,
    returned in API responses, or stored in the database.
  * A missing or empty token causes the fetch to raise ApifyError, which
    the ingestion layer catches and logs without exposing the token.
"""

import json
import logging
import os
import re
import time

try:
    import requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

from backend.apify.config import (
    APIFY_ACTOR_ID,
    APIFY_API_BASE,
    APIFY_API_TOKEN,
    APIFY_MAX_POSTS,
    APIFY_SOURCE_URL,
    APIFY_TIMEOUT,
)

logger = logging.getLogger("tce.apify.collector")

# Retry settings for transient Apify failures
_MAX_POLL_SECONDS = 300  # 5 minutes max wait for a run to finish
_POLL_INTERVAL = 10


class ApifyError(Exception):
    """Raised when Apify returns an error or the token is missing."""


def _headers():
    """Build auth headers WITHOUT logging the token."""
    if not APIFY_API_TOKEN:
        raise ApifyError("APIFY_API_TOKEN environment variable is not set.")
    return {"Authorization": f"Bearer {APIFY_API_TOKEN}"}


def _safe_actor_id():
    """Return the actor ID with the slash replaced for URL embedding."""
    return APIFY_ACTOR_ID.replace("/", "~")


def _extract_post_id(url):
    """Extract LinkedIn activity numeric ID from a post URL."""
    if not url:
        return None
    m = re.search(r"activity[:\-/?=_]*(\d+)", str(url), re.I)
    return m.group(1) if m else None


def _normalize_post(raw):
    """Normalize a raw Apify post dict to a canonical shape.

    Returns a dict with known keys only; unknown keys are ignored.
    """
    url = raw.get("url") or raw.get("postUrl") or raw.get("linkedInUrl") or ""
    text = raw.get("text") or raw.get("postText") or raw.get("content") or ""
    post_id = (
        raw.get("id")
        or raw.get("activityUrn")
        or raw.get("postId")
        or _extract_post_id(url)
        or ""
    )
    # Derive activity ID from URN if possible
    activity_id = _extract_post_id(url) or _extract_post_id(str(post_id))

    return {
        "apify_post_id": str(post_id) if post_id else None,
        "activity_id": activity_id,
        "post_url": url or None,
        "text": text,
        "likes": raw.get("likesCount") or raw.get("likes") or 0,
        "comments": raw.get("commentsCount") or raw.get("comments") or 0,
        "shares": raw.get("sharesCount") or raw.get("shares") or 0,
        "posted_at": raw.get("date") or raw.get("postedAt") or raw.get("timestamp"),
        # Pagination cursor from Apify (actor-specific field name varies)
        "cursor": raw.get("cursor") or raw.get("paginationToken") or None,
        "_raw": raw,  # kept for debugging; never logged in full
    }


# ---------------------------------------------------------------------------
# Mock collector (used in tests and when APIFY_ENABLED=false)
# ---------------------------------------------------------------------------

MOCK_POSTS = [
    {
        "apify_post_id": "mock-001",
        "activity_id": "7214000000000001",
        "post_url": "https://www.linkedin.com/feed/update/urn:li:activity:7214000000000001/",
        "text": (
            "TCE Department of Computer Science organised a Workshop on "
            "Machine Learning and Deep Learning on 10 September 2026. "
            "Students gained hands-on experience with Python and TensorFlow."
        ),
        "likes": 120,
        "comments": 15,
        "shares": 5,
        "posted_at": "2026-09-10",
        "cursor": "cursor-after-001",
    },
    {
        "apify_post_id": "mock-002",
        "activity_id": "7214000000000002",
        "post_url": "https://www.linkedin.com/feed/update/urn:li:activity:7214000000000002/",
        "text": (
            "Congratulations to our students for winning the National Level "
            "Technical Symposium 2026! The ECE department students bagged the "
            "first prize in the paper presentation event."
        ),
        "likes": 250,
        "comments": 40,
        "shares": 18,
        "posted_at": "2026-09-15",
        "cursor": "cursor-after-002",
    },
    {
        "apify_post_id": "mock-003",
        "activity_id": "7214000000000003",
        "post_url": "https://www.linkedin.com/feed/update/urn:li:activity:7214000000000003/",
        "text": (
            "TCE hosted a Guest Lecture on Cyber Security by industry expert "
            "Mr. Rajan from ISRO on 20 September 2026. Faculty and students "
            "interacted with the expert on current security challenges."
        ),
        "likes": 90,
        "comments": 12,
        "shares": 7,
        "posted_at": "2026-09-20",
        "cursor": "cursor-after-003",
    },
    {
        "apify_post_id": "mock-004",
        "activity_id": "7214000000000004",
        "post_url": "https://www.linkedin.com/feed/update/urn:li:activity:7214000000000004/",
        "text": (
            "Happy Diwali wishes to all from Thiagarajar College of Engineering! "
            "May this festival of lights bring joy and prosperity."
        ),
        "likes": 500,
        "comments": 80,
        "shares": 30,
        "posted_at": "2026-10-01",
        "cursor": "cursor-after-004",
    },
    {
        "apify_post_id": "mock-005",
        "activity_id": "7214000000000005",
        "post_url": "https://www.linkedin.com/feed/update/urn:li:activity:7214000000000005/",
        "text": (
            "TCE Department of Mechanical Engineering organised a Faculty Development "
            "Programme (FDP) on Advanced Manufacturing Technologies from "
            "25 September to 29 September 2026. Twenty faculty members participated."
        ),
        "likes": 75,
        "comments": 8,
        "shares": 3,
        "posted_at": "2026-09-25",
        "cursor": "cursor-after-005",
    },
]


def fetch_posts_mock(max_posts=None, cursor=None):
    """Return mock posts for testing without calling Apify."""
    limit = max_posts or APIFY_MAX_POSTS
    posts = MOCK_POSTS[:limit]
    # Apply cursor-based resume: skip posts up to the cursor
    if cursor:
        idx = next(
            (i for i, p in enumerate(MOCK_POSTS) if p.get("cursor") == cursor),
            None,
        )
        if idx is not None:
            posts = MOCK_POSTS[idx + 1:idx + 1 + limit]
        else:
            posts = []
    return posts


# ---------------------------------------------------------------------------
# Real Apify collector
# ---------------------------------------------------------------------------

def _run_actor(max_posts, cursor=None):
    """Trigger an Apify actor run and return the run ID."""
    if not _HAS_REQUESTS:
        raise ApifyError("requests library is not installed.")

    actor = _safe_actor_id()
    url = f"{APIFY_API_BASE}/acts/{actor}/runs"
    body = {
        "startUrls": [{"url": APIFY_SOURCE_URL}],
        "maxPosts": max_posts,
    }
    if cursor:
        body["paginationToken"] = cursor

    resp = requests.post(
        url, json=body, headers=_headers(), timeout=APIFY_TIMEOUT
    )
    if resp.status_code not in (200, 201):
        raise ApifyError(
            f"Apify actor start failed: HTTP {resp.status_code}"
        )
    data = resp.json()
    return data.get("data", {}).get("id")


def _wait_for_run(run_id):
    """Poll until the run finishes. Return final status string."""
    if not _HAS_REQUESTS:
        raise ApifyError("requests library is not installed.")

    deadline = time.time() + _MAX_POLL_SECONDS
    while time.time() < deadline:
        resp = requests.get(
            f"{APIFY_API_BASE}/actor-runs/{run_id}",
            headers=_headers(),
            timeout=APIFY_TIMEOUT,
        )
        if resp.status_code != 200:
            raise ApifyError(f"Apify run status check failed: HTTP {resp.status_code}")
        run = resp.json().get("data", {})
        status = run.get("status", "")
        if status in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
            return status
        time.sleep(_POLL_INTERVAL)
    raise ApifyError(f"Apify run {run_id} did not finish within {_MAX_POLL_SECONDS}s")


def _fetch_dataset(run_id):
    """Fetch the default dataset items from a completed Apify run."""
    if not _HAS_REQUESTS:
        raise ApifyError("requests library is not installed.")

    resp = requests.get(
        f"{APIFY_API_BASE}/actor-runs/{run_id}/dataset/items",
        headers=_headers(),
        params={"format": "json", "clean": "true"},
        timeout=APIFY_TIMEOUT,
    )
    if resp.status_code != 200:
        raise ApifyError(
            f"Apify dataset fetch failed: HTTP {resp.status_code}"
        )
    return resp.json()


def fetch_posts(max_posts=None, cursor=None):
    """Fetch up to `max_posts` LinkedIn posts from Apify.

    Args:
        max_posts: Maximum posts to retrieve (defaults to APIFY_MAX_POSTS).
        cursor: Continuation cursor from the last run (for checkpoint resume).

    Returns:
        List of normalized post dicts.

    Raises:
        ApifyError: If the API call fails or the token is missing.
    """
    limit = max_posts or APIFY_MAX_POSTS
    logger.info("Starting Apify fetch: actor=%s max=%d cursor=%s",
                APIFY_ACTOR_ID, limit, "present" if cursor else "none")

    run_id = _run_actor(limit, cursor)
    if not run_id:
        raise ApifyError("Apify did not return a run ID.")

    logger.info("Apify run started: run_id=%s", run_id)
    status = _wait_for_run(run_id)

    if status != "SUCCEEDED":
        raise ApifyError(f"Apify run {run_id} ended with status: {status}")

    raw_items = _fetch_dataset(run_id)
    posts = [_normalize_post(item) for item in (raw_items or [])]
    logger.info("Apify fetched %d posts (run_id=%s)", len(posts), run_id)
    return posts, run_id
