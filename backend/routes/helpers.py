"""Shared helpers for Flask API blueprints."""

import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from flask import jsonify, request

logger = logging.getLogger("tce-api")

ACCESS_LOG = False  # per-request log line


def setup_logging(app):
    if not app.logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s"
        ))
        app.logger.addHandler(handler)
    app.logger.setLevel(getattr(app, "LOG_LEVEL", logging.INFO))


def error_response(message, status=400, **extra):
    payload = {"error": message}
    payload.update(extra)
    return jsonify(payload), status


def ok(payload, status=200):
    return jsonify(payload), status


def paginate_args():
    """Validate page/page_size with caps; returns (offset, limit)."""
    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 20))
    except (TypeError, ValueError):
        raise ValueError("page and page_size must be integers")

    if page < 1:
        raise ValueError("page must be >= 1")
    if page_size < 1:
        raise ValueError("page_size must be >= 1")
    return (page - 1) * page_size, page_size


def page_response(items, total, page, page_size):
    return {
        "data": items,
        "total": total,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "pages": (total + page_size - 1) // page_size if page_size else 0,
        },
    }


def log_request():
    if ACCESS_LOG:
        logger.info("%s %s args=%s", request.method, request.path, dict(request.args))