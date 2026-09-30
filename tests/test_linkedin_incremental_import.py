"""Tests for the append-only incremental LinkedIn workbook importer.

These build a throwaway staging DB from scratch, so they exercise the genuine
first-import path (owner post created in the same run) as well as idempotency.
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database import linkedin_incremental_import as imp  # noqa: E402
from backend.database.linkedin_incremental_import import (  # noqa: E402
    EXISTING_DUPLICATE,
    NEW_FILE_DUPLICATE,
    NEW_POST,
    get_staging_connection,
    import_workbook,
)


def _write_workbook(path, texts, sheet="All posts", banner="Posts from June 2026 - September 2026"):
    """Write a one-column sheet shaped like the real faculty export:
    a blank spacer row, a short title banner, then one post per row."""
    import pandas as pd

    rows = [[None], [banner]] + [[t] for t in texts]
    with pd.ExcelWriter(path) as xl:
        pd.DataFrame(rows).to_excel(xl, sheet_name=sheet, index=False, header=False)
    return path


def _wb(tmp_path, name, texts, sheet="All posts", banner="Posts from June 2026 - September 2026"):
    return _write_workbook(tmp_path / name, texts, sheet=sheet, banner=banner)


def _counts(db):
    conn = get_staging_connection(db)
    try:
        def n(table):
            if conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                            (table,)).fetchone() is None:
                return 0
            return conn.execute("SELECT COUNT(*) c FROM %s" % table).fetchone()["c"]
        return {"posts": n("linkedin_posts"), "occ": n("linkedin_post_occurrences")}
    finally:
        conn.close()


def test_first_import_creates_posts_and_occurrences(tmp_path):
    db = str(tmp_path / "s.db")
    wb = _wb(tmp_path, "batch1.xlsx", ["Alpha post text one", "Beta post text two"])

    report = import_workbook(wb, db_path=db)

    assert report["classification"] == {NEW_POST: 2}
    assert report["staging_after"]["canonical_posts"] == 2
    # one occurrence per incoming row
    assert report["staging_after"]["occurrences"] == 2
    assert len(report["title_banners_skipped"]) == 1


def test_banner_rows_are_not_treated_as_posts(tmp_path):
    db = str(tmp_path / "s.db")
    wb = _wb(tmp_path, "batch1.xlsx", ["Alpha post text one", "Beta post text two"])

    report = import_workbook(wb, db_path=db)

    # 2 real posts despite 1 banner + header rows in the sheet
    assert report["incoming_rows"] == 2
    assert report["classification"] == {NEW_POST: 2}


def test_second_import_is_idempotent(tmp_path):
    db = str(tmp_path / "s.db")
    wb = _wb(tmp_path, "batch1.xlsx", ["Alpha post text one", "Beta post text two"])
    import_workbook(wb, db_path=db)
    before = _counts(db)

    report = import_workbook(wb, db_path=db)

    assert report["classification"] == {EXISTING_DUPLICATE: 2}
    assert _counts(db) == before


def test_same_text_in_different_workbook_keeps_both_occurrences(tmp_path):
    """The workbook is part of the occurrence natural key."""
    db = str(tmp_path / "s.db")
    text = "The department organised a workshop on deep learning."
    import_workbook(_wb(tmp_path, "batch1.xlsx", [text]), db_path=db)
    report = import_workbook(_wb(tmp_path, "batch2.xlsx", [text]), db_path=db)

    assert report["classification"] == {EXISTING_DUPLICATE: 1}
    # one canonical post, but an occurrence from each workbook
    assert _counts(db) == {"posts": 1, "occ": 2}


def test_within_file_near_duplicate_resolves_to_new_owner(tmp_path):
    """Regression: a near-duplicate of a post created in the SAME run must still
    record its occurrence against the owner created moments earlier."""
    db = str(tmp_path / "s.db")
    base = ("The Department of Electrical Engineering conducted a five day boot camp "
            "on artificial intelligence for the students of the third year during "
            "August 2026 with industry experts.")
    # ~97% similar: swap a couple of words, keep length
    near = ("The Department of Electrical Engineering conducted a five day bootcamp "
            "on artificial intelligence for the students of third year during "
            "August 2026 with industry experts.")

    report = import_workbook(_wb(tmp_path, "batch1.xlsx", [base, near]), db_path=db)

    assert report["classification"][NEW_FILE_DUPLICATE] == 1
    assert report["classification"][NEW_POST] == 1
    counts = _counts(db)
    # 1 canonical post, 2 occurrences -> the duplicate was NOT dropped
    assert counts == {"posts": 1, "occ": 2}

    conn = get_staging_connection(db)
    try:
        rows = conn.execute(
            "SELECT linkedin_post_id, duplicate_flag, duplicate_reason "
            "FROM linkedin_post_occurrences ORDER BY id").fetchall()
    finally:
        conn.close()
    assert len({r["linkedin_post_id"] for r in rows}) == 1
    assert any(r["duplicate_flag"] == 1 for r in rows)


def test_within_file_exact_duplicate_occurs_once_under_one_post(tmp_path):
    db = str(tmp_path / "s.db")
    text = "The department celebrated a cultural day with performances by students."

    report = import_workbook(_wb(tmp_path, "batch1.xlsx", [text, text]), db_path=db)

    assert report["classification"][NEW_FILE_DUPLICATE] == 1
    assert _counts(db) == {"posts": 1, "occ": 2}


def test_dry_run_writes_nothing(tmp_path):
    db = str(tmp_path / "s.db")
    wb = _wb(tmp_path, "batch1.xlsx", ["Alpha post text one", "Beta post text two"])

    report = import_workbook(wb, db_path=db, dry_run=True)

    assert report["dry_run"] is True
    assert _counts(db) == {"posts": 0, "occ": 0}


def test_provenance_records_the_workbook_name(tmp_path):
    db = str(tmp_path / "s.db")
    import_workbook(_wb(tmp_path, "batch1.xlsx", ["Alpha post text one"]), db_path=db)

    conn = get_staging_connection(db)
    try:
        r = conn.execute(
            "SELECT source_workbook FROM linkedin_posts").fetchone()
        assert r["source_workbook"] == "batch1.xlsx"
    finally:
        conn.close()
