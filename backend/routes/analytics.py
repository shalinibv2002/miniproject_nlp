"""Analytics endpoints (Phase 9 analytics exposed over HTTP)."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from flask import Blueprint, request

from backend.analytics import stakeholder, linkedin_visibility, data_quality
from backend.analytics import public as public_analytics
from backend.database.category_catalog import (
    resolve_departmental_category, resolve_general_category,
)
from backend.database.period_catalog import normalize_period
from backend.routes.helpers import error_response, ok


def _period_arg(name="academic_year"):
    """Normalise the single-period query argument, validating short keys."""
    value = (request.args.get(name) or request.args.get("period") or "").strip()
    if not value:
        return None
    normalized = normalize_period(value)
    if normalized is None:
        raise ValueError("academic_year must be a supported academic year or 'Before 2021'")
    return normalized

bp = Blueprint("analytics", __name__, url_prefix="/api/analytics")


@bp.get("/overview")
def get_overview():
    return ok(public_analytics.overview())


@bp.get("/general")
def get_general():
    """The institution-wide (General) dashboard payload.

    Supports an optional ``general_category`` code so every series in the
    General dashboard reflects the active selection consistently, and an
    optional ``academic_year`` (short key or ``Before 2021``) to report one
    resolved period for the whole dashboard.
    """
    general_category = (request.args.get("general_category") or "").strip() or None
    if general_category and not resolve_general_category(general_category):
        return error_response("general_category must be a supported General Category", 400)
    try:
        academic_year = _period_arg()
    except ValueError as exc:
        return error_response(str(exc), 400)
    return ok(public_analytics.general_analytics(
        general_category=general_category, academic_year=academic_year))


@bp.get("/department")
def get_department():
    """The Department dashboard payload.

    Without ``department`` the overview of the exactly-17 public departments is
    returned; with one canonical department name only that department is
    reported.  ``General`` is never a valid department option.  An optional
    ``departmental_category`` code restricts every series consistently, and an
    optional ``academic_year`` restricts every series to one resolved period.
    """
    department = (request.args.get("department") or "").strip() or None
    departmental_category = (request.args.get("departmental_category") or "").strip() or None
    if departmental_category and not resolve_departmental_category(departmental_category):
        return error_response("departmental_category must be a supported Departmental Category", 400)
    try:
        academic_year = _period_arg()
    except ValueError as exc:
        return error_response(str(exc), 400)
    try:
        return ok(public_analytics.department_analytics(
            department=department, departmental_category=departmental_category,
            academic_year=academic_year))
    except ValueError as exc:
        return error_response(str(exc), 400)


@bp.get("/yearly")
def get_yearly():
    return ok({"yearly_breakdown": public_analytics.yearly_counts()})


@bp.get("/departments")
def get_departments():
    return ok({"summary": public_analytics.department_summary()})


@bp.get("/categories")
def get_categories():
    summary = public_analytics.category_summary()
    # Keep the pre-Step-7 array response for current clients.  The optional
    # matrix makes the clean dashboard trend available without another route.
    if request.args.get("include_trend") in ("1", "true", "True"):
        return ok({"summary": summary,
                   "year_category_breakdown": public_analytics.year_category_breakdown()})
    return ok(summary)


@bp.get("/stakeholders")
def get_stakeholders():
    return ok(stakeholder.stakeholder_summary())


@bp.get("/linkedin")
def get_linkedin():
    return ok(linkedin_visibility.linkedin_summary())


@bp.get("/data-quality")
def get_data_quality():
    return ok(data_quality.data_quality())
