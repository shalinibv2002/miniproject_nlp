"""Natural-language query endpoint (Phase 12)."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from flask import Blueprint, request

from backend.nlp.query_engine import answer_question
from backend.routes.helpers import error_response, ok

bp = Blueprint("query", __name__, url_prefix="/api")


@bp.route("/query", methods=["GET", "POST"])
def run_query():
    if request.method == "POST":
        body = request.get_json(silent=True) or {}
        question = (
            body.get("question")
            or request.args.get("q")
            or request.args.get("question")
            or ""
        ).strip()
    else:
        question = (
            request.args.get("q")
            or request.args.get("question")
            or ""
        ).strip()

    if not question:
        return error_response("missing 'question' (provide JSON body or 'q' query param)", 400)
    if len(question) > 500:
        return error_response("question too long (max 500 chars)", 400)
    result = answer_question(question)
    # Keep implementation details out of the public HTTP contract.
    return ok({key: result[key] for key in (
        "question", "status", "answer", "count", "activities",
        "comparison", "rows", "chart", "criteria", "detail",
    ) if key in result})
