"""Collection endpoint (re-runs the raw-record ingestion pipeline)."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import traceback

from flask import Blueprint, request

from backend.routes.helpers import error_response, ok

bp = Blueprint("collection", __name__, url_prefix="/api/collection")


@bp.post("/run")
def run_collection():
    """Re-run cleaning/validation/dedup/load on saved raw records.

    This is offline ingestion — it does not re-crawl tce.edu. Crawling is
    triggered via `python -m backend.collectors.tce_events_collector`.
    """
    body = request.get_json(silent=True) or {}
    raw_dir = body.get("raw_dir")
    if raw_dir and not isinstance(raw_dir, str):
        return error_response("raw_dir must be a string", 400)
    try:
        from backend.database.pipeline import run_pipeline
        result = run_pipeline(raw_dirs=[raw_dir] if raw_dir else None)
        return ok({
            "status": "completed",
            "result": result,
        })
    except Exception:
        return error_response("collection run failed", 500,
                              detail=traceback.format_exc(limit=5))