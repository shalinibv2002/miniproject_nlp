"""Step 5 candidate-only academic-year resolution and quality audit."""

from collections import Counter

from backend.database.init_db import get_connection, init_db
from backend.extraction.activity_candidate_extractor import (
    academic_year, extract_academic_year_context, extract_date, source_is_non_activity,
)
from backend.nlp.candidate_classify import classification_report


def _resolution_for(row, boundary_month=8):
    """Return (year, reason) only for evidence explicitly tied to this candidate."""
    evidence = row["evidence_text"] or ""
    # NIRF submitted-institute data lists reporting years and intake figures;
    # it is not an activity block even when it contains an Academic Year label.
    if "submitted institute data for nirf" in evidence.lower():
        return None, None
    if row["activity_date"]:
        assigned = academic_year(row["activity_date"], boundary_month)
        if assigned:
            return assigned, "EXACT_ACTIVITY_DATE"
    block_date, _ = extract_date(evidence)
    if block_date:
        assigned = academic_year(block_date, boundary_month)
        if assigned:
            return assigned, "ACTIVITY_BLOCK_DATE"
    block_context = extract_academic_year_context(evidence)
    if block_context:
        return block_context, "ACADEMIC_YEAR_CONTEXT"
    # This recognises only an explicitly-labelled Annual Report period, never
    # a bare year in a filename, URL, copyright footer, or generic title.
    report_context = extract_academic_year_context(row["page_title"] or "")
    if report_context and "annual report" in (row["page_title"] or "").lower():
        return report_context, "ANNUAL_REPORT_CONTEXT"
    return None, None


def resolve_academic_years(conn=None, extraction_run_id=4, boundary_month=8):
    """Resolve only currently-null years and retain a candidate-layer audit row."""
    init_db()
    own = conn is None
    conn = conn or get_connection()
    try:
        rows = conn.execute(
            """SELECT c.*, o.page_title, o.source_url FROM activity_candidates c
               JOIN raw_source_occurrences o ON o.id=c.source_occurrence_id
               WHERE c.extraction_run_id=? AND c.academic_year IS NULL ORDER BY c.id""",
            (extraction_run_id,),
        ).fetchall()
        resolved = Counter()
        for row in rows:
            assigned, reason = _resolution_for(row, boundary_month)
            if not assigned:
                continue
            conn.execute("UPDATE activity_candidates SET academic_year=?, updated_at=datetime('now') WHERE id=? AND academic_year IS NULL",
                         (assigned, row["id"]))
            conn.execute(
                """INSERT OR REPLACE INTO candidate_academic_year_resolutions
                   (candidate_id, original_academic_year, resolved_academic_year, resolution_reason)
                   VALUES (?, NULL, ?, ?)""", (row["id"], assigned, reason),
            )
            resolved[reason] += 1
        conn.commit()
        return dict(resolved)
    finally:
        if own:
            conn.close()


def _quality_for(row):
    reasons = []
    source = f"{row['source_url'] or ''} {row['page_title'] or ''}"
    evidence = row["evidence_text"] or ""
    title = (row["title"] or "").strip()
    category_count = len(set((row["final_categories"] or "").split(",")) - {""})
    if source_is_non_activity(row["source_url"], row["page_title"]):
        return "NON_ACTIVITY", "ADMINISTRATIVE_OR_POLICY_SOURCE"
    if row["source_url"].rstrip("/") == "https://www.tce.edu" and len(evidence) > 250:
        reasons.append("HOMEPAGE_MIXED_CONTENT")
    if category_count >= 5:
        reasons.append("MANY_UNRELATED_FINAL_CATEGORIES")
    if len(evidence) > 700:
        reasons.append("OVERSIZED_ACTIVITY_BLOCK")
    if len(title.split()) <= 1 or title.lower() in {"he", "she", "campus", "institution"}:
        reasons.append("GENERIC_OR_TRUNCATED_TITLE")
    if "activities list" in evidence.lower() or "event themes:" in evidence.lower():
        reasons.append("COLLAPSED_ACTIVITY_LIST")
    return ("REVIEW", "; ".join(reasons)) if reasons else ("GOOD", None)


def review_candidate_quality(conn=None, extraction_run_id=4):
    """Flag source/block quality without changing extracted or classified data."""
    init_db()
    own = conn is None
    conn = conn or get_connection()
    try:
        rows = conn.execute(
            """SELECT c.*, o.source_url, o.page_title, GROUP_CONCAT(cc.final_category) AS final_categories
               FROM activity_candidates c JOIN raw_source_occurrences o ON o.id=c.source_occurrence_id
               LEFT JOIN candidate_classifications cc ON cc.candidate_id=c.id
               WHERE c.extraction_run_id=? GROUP BY c.id ORDER BY c.id""", (extraction_run_id,)
        ).fetchall()
        counts = Counter()
        for row in rows:
            status, reason = _quality_for(row)
            conn.execute(
                """INSERT OR REPLACE INTO candidate_quality_reviews
                   (candidate_id, quality_status, quality_reason) VALUES (?, ?, ?)""",
                (row["id"], status, reason),
            )
            counts[status] += 1
        conn.commit()
        return dict(counts)
    finally:
        if own:
            conn.close()


def quality_report(conn, extraction_run_id=4):
    """Return database-derived Step 5 report data without applying rules again."""
    report = classification_report(conn, extraction_run_id)
    resolutions = dict(conn.execute(
        """SELECT resolution_reason, COUNT(*) FROM candidate_academic_year_resolutions r
           JOIN activity_candidates c ON c.id=r.candidate_id WHERE c.extraction_run_id=?
           GROUP BY resolution_reason""", (extraction_run_id,)
    ).fetchall())
    quality = dict(conn.execute(
        """SELECT q.quality_status, COUNT(*) FROM candidate_quality_reviews q
           JOIN activity_candidates c ON c.id=q.candidate_id WHERE c.extraction_run_id=?
           GROUP BY q.quality_status""", (extraction_run_id,)
    ).fetchall())
    return {**report, "resolution_reasons": resolutions, "quality_statuses": quality}
