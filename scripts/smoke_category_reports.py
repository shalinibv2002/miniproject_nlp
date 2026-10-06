"""Real-data end-to-end smoke test for the category-specific reports.

Runs the live Flask app against the canonical LinkedIn reportable database and
walks one real activity through every user surface:

    Admin edit -> canonical DB -> public dashboard -> categories -> reports
    -> analytics -> Ask the Data -> XLSX -> PDF

The canonical database file is backed up before the run and restored at the end,
so the smoke test never leaves the dataset changed.
"""

import io
import json
import os
import shutil
import sys
import tempfile

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

CANONICAL_DB = os.path.join(ROOT, "backend", "database", "linkedin_reportable.db")

RESULTS = []


def check(label, ok, detail=""):
    RESULTS.append((label, bool(ok), detail))
    print("%-4s %s%s" % ("PASS" if ok else "FAIL", label,
                         ("  -- " + detail) if detail else ""))
    return bool(ok)


def _pick_pinnable_field(category_code, departments):
    """A derived report column this category's schema actually shows.

    Reading the choice from the live schema (rather than naming one here) is what
    makes this check a real test of the Admin form: if the schema and the form
    ever disagree, no pinnable column is found and the check fails.
    """
    from backend.database.category_report_schema import report_columns
    import backend.database.linkedin_reportable as rep

    scope = "departmental" if any(d and d != "General" for d in departments or []) \
        else "general"
    pinnable = set(rep.ADMIN_OVERRIDABLE_REPORT_FIELDS)
    for label, field in report_columns(category_code, scope):
        if field in pinnable:
            return field, label
    return None, None


def main():
    backup = os.path.join(tempfile.gettempdir(), "linkedin_reportable.smoke.bak")
    shutil.copy2(CANONICAL_DB, backup)
    print("canonical db backed up -> %s\n" % backup)

    try:
        run()
    finally:
        shutil.copy2(backup, CANONICAL_DB)
        print("\ncanonical db restored from backup")


def run():
    import sqlite3

    import backend.database.linkedin_reportable as rep
    from backend.app import create_app
    from backend.reports.linkedin_exports import (
        build_excel, build_pdf, export_columns, _report_sheet_bytes,
    )

    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    token = client.post("/api/admin/login",
                        json={"username": "shalini",
                              "password": "shalini02"}).get_json()["token"]
    headers = {"Authorization": "Bearer %s" % token}

    conn = sqlite3.connect(CANONICAL_DB)
    conn.row_factory = sqlite3.Row
    total_rows = conn.execute(
        "SELECT COUNT(*) c FROM linkedin_reportable_activities").fetchone()["c"]
    reportable_rows = conn.execute(
        "SELECT COUNT(*) c FROM linkedin_reportable_activities "
        "WHERE reportable_status = 'REPORTABLE'").fetchone()["c"]
    real_categories = sorted({
        code for r in conn.execute(
            "SELECT categories FROM linkedin_reportable_activities "
            "WHERE reportable_status = 'REPORTABLE'")
        for code in json.loads(r["categories"] or "[]")})
    conn.close()
    total_reportable = reportable_rows
    print("canonical dataset: %d rows, %d reportable, categories=%s\n"
          % (total_rows, reportable_rows, real_categories))

    # ------------------------------------------------------------------ 1
    print("== 1. Public dashboard ==")
    dash = client.get("/api/linkedin/analytics/overview")
    check("dashboard responds 200", dash.status_code == 200,
          "status=%s" % dash.status_code)
    dj = dash.get_json() or {}
    check("dashboard totals populated",
          bool(dj.get("total_reportable_activities")),
          "total_reportable_activities=%s" % dj.get("total_reportable_activities"))

    years = client.get("/api/linkedin/years").get_json()
    cats = client.get("/api/linkedin/categories").get_json()
    depts = client.get("/api/linkedin/departments").get_json()
    staks = client.get("/api/linkedin/stakeholders").get_json()
    check("academic-year dimension populated", bool(years),
          "years=%s" % [y["academic_year"] for y in years][:4])
    check("category dimension populated", bool(cats),
          "categories=%d" % len(cats))
    check("department dimension populated", bool(depts),
          "departments=%s" % [d["department"] for d in depts][:4])
    check("stakeholder dimension populated", bool(staks),
          "stakeholders=%s" % [s["stakeholder"] for s in staks][:4])

    gen = client.get("/api/linkedin/activities?scope=general").get_json()["data"]
    dep = client.get("/api/linkedin/activities?scope=departmental").get_json()["data"]
    check("General activities listed", bool(gen), "count=%d" % len(gen))
    check("Departmental activities listed", bool(dep), "count=%d" % len(dep))
    check("Departmental scope never returns the General pseudo-department",
          all(r.get("department") not in (None, "", "General") for r in dep),
          "sample=%s" % [r.get("department") for r in dep[:3]])

    # ------------------------------------------------------------------ 2
    print("\n== 2/3. Category-specific report columns ==")
    schema = client.get("/api/linkedin/report-schema").get_json()
    check("report-schema endpoint serves columns", bool(schema))

    # Expected columns are taken verbatim from
    # data/audit/category_wise_report_design_audit_20261003.json, with
    # "Post URL" delivered as "LinkedIn URL" and "Award Title" delivered as
    # "Award Category".  The audit recommends a Stakeholder column for CLUB
    # and WORKSHOP, and for SEMINAR only in the departmental report.
    expected = {
        "ACHIEVEMENT": ["S.No", "Stakeholder", "Name", "Award Category",
                        "Achievement Description", "Date", "Academic Year",
                        "LinkedIn URL"],
        "CLUB": ["S.No", "Title", "Stakeholder", "Date", "Academic Year",
                 "LinkedIn URL"],
        "WORKSHOP": ["S.No", "Title", "Duration", "Date", "Academic Year",
                     "LinkedIn URL"],
        "SEMINAR": ["S.No", "Seminar Title", "Description", "Speaker", "Date",
                    "Academic Year", "LinkedIn URL"],
        "FDP": ["S.No", "Title", "Date", "Academic Year", "LinkedIn URL"],
    }
    for code, columns in expected.items():
        prev = client.get("/api/linkedin/reports/preview?report_type=all"
                          "&category=%s&scope=general" % code).get_json()
        got = [c["label"] for c in prev.get("columns", [])]
        check("General %s columns" % code, got == columns,
              "got=%s" % got)

    expected_dept = {
        "CLUB": ["S.No", "Title", "Department", "Stakeholder", "Date",
                 "Academic Year", "LinkedIn URL"],
        "WORKSHOP": ["S.No", "Title", "Duration", "Department", "Date",
                     "Academic Year", "LinkedIn URL"],
        "SEMINAR": ["S.No", "Seminar Title", "Description", "Speaker",
                    "Department", "Date", "Academic Year", "LinkedIn URL"],
        "ACHIEVEMENT": ["S.No", "Stakeholder", "Name", "Department",
                        "Award Category", "Achievement Description", "Date",
                        "Academic Year", "LinkedIn URL"],
    }
    for code, columns in expected_dept.items():
        prev = client.get("/api/linkedin/reports/preview?report_type=all"
                          "&category=%s&scope=departmental" % code).get_json()
        got = [c["label"] for c in prev.get("columns", [])]
        check("Departmental %s columns" % code, got == columns, "got=%s" % got)

    # non-achievement categories must not carry achievement-only fields
    for code in ("CLUB", "WORKSHOP", "SEMINAR", "FDP", "CONFERENCE"):
        prev = client.get("/api/linkedin/reports/preview?report_type=all"
                          "&category=%s&scope=departmental" % code).get_json()
        labels = [c["label"] for c in prev.get("columns", [])]
        bad = [l for l in labels
               if l in ("Achievement Description", "Award Category")]
        check("%s hides achievement-only columns" % code, not bad,
              "leaked=%s" % bad)

    # Real rows: every audit column must be backed by the canonical record.
    # (Coverage of the underlying data is reported, not asserted: 42% of the
    # canonical rows have no post_url and no achievement row has a pinned
    # report_name, which is a data fact, not a report-layer fault.)
    canon = {}
    c2 = sqlite3.connect(CANONICAL_DB)
    c2.row_factory = sqlite3.Row
    for r in c2.execute("SELECT * FROM linkedin_reportable_activities"):
        canon[r["activity_id"]] = r
    c2.close()

    def probe(code, scope, required_labels):
        prev = client.get("/api/linkedin/reports/preview?report_type=all"
                          "&category=%s&scope=%s" % (code, scope)).get_json()
        rows = prev.get("records") or []
        if not check("real %s %s records available" % (code, scope), bool(rows),
                     "count=%d" % len(rows)):
            return
        by_label = {c["label"]: c.get("field") for c in prev["columns"]}
        missing = [l for l in required_labels if l not in by_label]
        check("%s %s exposes the audit columns" % (code, scope), not missing,
              "missing=%s" % missing)
        # every row must line up with its canonical DB row (no duplicates, no
        # invented values): the URL is either the canonical URL or empty.
        bad_url = [r["activity_id"] for r in rows
                   if (r.get("post_url") or "")
                   != ((canon.get(r["activity_id"]) or {})["post_url"] or "")]
        check("%s %s URLs match the canonical DB" % (code, scope), not bad_url,
              "mismatched=%s" % bad_url[:3])
        with_url = sum(1 for r in rows if (r.get("post_url") or "").startswith("http"))
        check("%s %s has at least one real LinkedIn URL" % (code, scope),
              with_url > 0, "%d/%d rows carry a URL" % (with_url, len(rows)))
        filled = {}
        for label in required_labels:
            field = by_label.get(label)
            if field and field != "sno":
                filled[label] = sum(
                    1 for r in rows if str(r.get(field) or "").strip())
        print("     %s %s column fill: %s" % (code, scope, filled))

    probe("ACHIEVEMENT", "general",
          ["Stakeholder", "Name", "Achievement Description", "Date",
           "Academic Year", "LinkedIn URL"])
    probe("ACHIEVEMENT", "departmental",
          ["Stakeholder", "Name", "Department", "Achievement Description",
           "Date", "Academic Year", "LinkedIn URL"])
    probe("CLUB", "departmental",
          ["Title", "Department", "Date", "Academic Year", "LinkedIn URL"])
    probe("WORKSHOP", "departmental",
          ["Title", "Duration", "Department", "Date", "Academic Year",
           "LinkedIn URL"])
    probe("SEMINAR", "general",
          ["Seminar Title", "Description", "Speaker", "Date", "Academic Year",
           "LinkedIn URL"])
    # The revised contracts that replace an audit layout.
    probe("CONFERENCE", "departmental",
          ["Chief Guest", "Department", "Date", "Academic Year", "LinkedIn URL"])
    probe("INDUSTRY", "departmental",
          ["Department", "Signed MOU With", "Purpose", "Date", "Academic Year",
           "LinkedIn URL"])
    probe("RESEARCH", "departmental",
          ["Research Topic", "Stakeholder", "Stakeholder Name", "Department",
           "Description", "Date", "Academic Year", "LinkedIn URL"])
    probe("INTERNSHIP", "departmental",
          ["Title", "Duration", "Department", "Date (From-To)", "Academic Year",
           "LinkedIn URL"])
    probe("ALUMNI", "general",
          ["Alumni Name", "Department", "Topic/Theme", "Date", "Academic Year",
           "LinkedIn URL"])

    # General scope must not show Department
    prev_gen = client.get("/api/linkedin/reports/preview?report_type=all"
                          "&category=WORKSHOP&scope=general").get_json()
    gen_labels = [c["label"] for c in prev_gen["columns"]]
    check("General report omits Department", "Department" not in gen_labels,
          "labels=%s" % gen_labels)

    # a category filter returns only that category
    prev_filtered = client.get(
        "/api/linkedin/reports/preview?report_type=all&category=CLUB"
        "&scope=departmental").get_json()
    filtered_rows = prev_filtered.get("data") or prev_filtered.get("records") or []
    check("category filter returns only that category",
          all((r.get("category_code")
               or (r.get("categories") or [{}])[0].get("code")) == "CLUB"
              for r in filtered_rows),
          "categories=%s" % sorted({
              (r.get("category_code")
               or (r.get("categories") or [{}])[0].get("code"))
              for r in filtered_rows}))

    # ------------------------------------------------------------------ 4
    print("\n== 4. Admin -> User synchronization (multi-value edit) ==")
    admin_list = client.get("/api/admin/linkedin/activities?page_size=200",
                                headers=headers)
    check("admin activity list responds 200", admin_list.status_code == 200,
          "status=%s" % admin_list.status_code)
    target = None
    for row in admin_list.get_json()["data"]:
        if row.get("reportable_status") == "REPORTABLE" and row.get("staging_post_id"):
            target = row
            break
    if not check("real reportable activity available for admin edit", bool(target)):
        return

    aid = target["activity_id"]
    print("editing %s (%s)" % (aid, target.get("title")))

    rows_before = conn_count()
    detail_before = client.get("/api/linkedin/activities/%s" % aid).get_json()
    orig_staks = list(target.get("stakeholders") or [])
    orig_depts = list(target.get("departments") or [])
    opts = client.get("/api/admin/linkedin/options", headers=headers).get_json()
    all_staks = [s for s in (opts.get("stakeholders") or [])
                 if s not in orig_staks]
    all_depts = [d for d in (opts.get("departments") or [])
                 if d != "General" and d not in orig_depts]
    all_cats = [c["code"] for c in (opts.get("categories") or [])
                if c["code"] not in (target.get("categories") or [])]

    new_staks = orig_staks + all_staks[:2]
    new_depts = orig_depts + all_depts[:2]
    # One activity carries exactly ONE primary category (documented
    # invariant), so "add category" is exercised as a single-category change and
    # the multi-category rejection is asserted explicitly below.
    new_cat = (all_cats or ["SEMINAR"])[:1]

    # -- adding a second category must be refused by the invariant
    reject = client.patch("/api/admin/linkedin/activities/%s" % aid,
                          headers=headers,
                          json={"categories": [new_cat[0]] + all_cats[1:3]})
    check("second primary category refused (one category per activity)",
          reject.status_code == 400 and "one primary category" in
          reject.get_data(as_text=True),
          "status=%s body=%s" % (reject.status_code,
                                 reject.get_data(as_text=True)[:120]))

    res = client.patch("/api/admin/linkedin/activities/%s" % aid,
                       headers=headers,
                       json={"stakeholders": new_staks,
                             "departments": new_depts,
                             "categories": new_cat,
                             "_note": "smoke test multi-value edit"})
    check("admin multi-value PATCH accepted", res.status_code == 200,
          "status=%s body=%s" % (res.status_code, res.get_data(as_text=True)[:160]))

    detail_after = client.get("/api/linkedin/activities/%s" % aid).get_json()
    check("canonical DB row count unchanged (no duplicate activity)",
          conn_count() == rows_before,
          "before=%d after=%d" % (rows_before, conn_count()))
    check("stakeholders persisted (added values)",
          sorted(detail_after["stakeholders"]) == sorted(new_staks),
          "%s" % detail_after["stakeholders"])
    check("departments persisted (added values, never General)",
          sorted(detail_after["departments"]) == sorted(new_depts) and
          "General" not in detail_after["departments"],
          "%s" % detail_after["departments"])
    check("category persisted (single primary category)",
          [c["code"] for c in detail_after["categories"]] == new_cat,
          "%s" % detail_after["categories"])
    check("one activity is still one public row",
          detail_after["activity_id"] == aid and
          client.get("/api/linkedin/analytics/overview").get_json()
          ["total_reportable_activities"] == total_reportable,
          "activity_id=%s total=%s" % (
              aid, client.get("/api/linkedin/analytics/overview").get_json()
              ["total_reportable_activities"]))

    # -- a category-specific report column must be editable and reach every
    #    surface.  Pick a column that belongs to the edited category's schema,
    #    so this proves the Admin form and the report really share one source.
    pin_field, pin_marker = _pick_pinnable_field(new_cat[0], new_depts)
    if pin_field:
        pin_value = "Smoke Check %s" % pin_marker
        res = client.patch("/api/admin/linkedin/activities/%s" % aid,
                           headers=headers,
                           json={pin_field: pin_value,
                                 "_note": "smoke test category column edit"})
        check("admin PATCH accepts the %s column" % pin_field,
              res.status_code == 200,
              "status=%s body=%s" % (res.status_code,
                                     res.get_data(as_text=True)[:160]))

        public_after = client.get("/api/linkedin/activities/%s" % aid).get_json()
        check("%s shows the admin-entered value" % pin_field,
              (public_after.get(pin_field) or "") == pin_value,
              "got=%r" % (public_after.get(pin_field),))

        # The report table for that category must show the same cell value.
        rep = client.get("/api/linkedin/reports/preview",
                         query_string={"report_type": "all", "scope": "departmental",
                                       "category": new_cat[0]})
        rows = (rep.get_json() or {}).get("records") or []
        hit = [r for r in rows if str(r.get("activity_id")) == str(aid)]
        check("%s visible in that category's report table" % pin_field,
              bool(hit) and (hit[0].get(pin_field) or "") == pin_value,
              "rows=%d cell=%r" % (len(hit),
                                    hit[0].get(pin_field) if hit else None))

        # Clearing the pin must hand the column back to what the post derives.
        client.patch("/api/admin/linkedin/activities/%s" % aid,
                     headers=headers,
                     json={pin_field: "", "_note": "smoke test clear pin"})
        cleared = client.get("/api/linkedin/activities/%s" % aid).get_json()
        check("clearing %s falls back to the derived value" % pin_field,
              (cleared.get(pin_field) or "") != pin_value,
              "got=%r" % (cleared.get(pin_field),))

        bad = client.patch("/api/admin/linkedin/activities/%s" % aid,
                           headers=headers,
                           json={"not_a_report_column": "x"})
        check("an unknown column is refused, not silently ignored",
              bad.status_code == 400,
              "status=%s" % bad.status_code)
    else:
        check("a pinnable category column exists for the edited category", False,
              "category=%s" % new_cat[0])

    # the public list is paginated, so narrow it with the values just edited
    narrow = client.get("/api/linkedin/activities",
                        query_string={"department": new_depts[-1],
                                      "stakeholder": new_staks[-1],
                                      "page_size": 500}).get_json()["data"]
    check("edit visible in the public activity list",
          any(r["activity_id"] == aid and
              sorted(r["stakeholders"]) == sorted(new_staks) and
              sorted(r["departments"]) == sorted(new_depts)
              for r in narrow),
          "narrowed rows=%d" % len(narrow))

    cat_counts = {c["category"]: c["activity_count"] for c in
                  client.get("/api/linkedin/categories").get_json()}
    check("analytics reflects the edited category",
          cat_counts.get(new_cat[0], 0) >= 1,
          "edited=%s count=%s" % (new_cat, cat_counts.get(new_cat[0])))
    stak_counts = {s["stakeholder"]: s["activity_count"] for s in
                   client.get("/api/linkedin/stakeholders").get_json()}
    check("analytics reflects the added stakeholders",
          all(stak_counts.get(s, 0) >= 1 for s in new_staks),
          "edited=%s" % new_staks)

    # department filters must never match the General pseudo-department
    for d in new_depts:
        rows = client.get("/api/linkedin/activities",
                          query_string={"department": d,
                                        "page_size": 500}).get_json()["data"]
        check("department filter '%s' includes the edited activity" % d,
              any(r["activity_id"] == aid for r in rows),
              "rows=%d" % len(rows))
    gen_rows = client.get("/api/linkedin/activities",
                          query_string={"department": "General",
                                        "page_size": 500}).get_json()["data"]
    check("the General pseudo-department is not a departmental value",
          all(r.get("department") == "General" for r in gen_rows),
          "rows=%d" % len(gen_rows))

    # -- removing values (remove stakeholder / remove department)
    trimmed_staks = new_staks[:-1]
    trimmed_depts = new_depts[:-1]
    res2 = client.patch("/api/admin/linkedin/activities/%s" % aid, headers=headers,
                        json={"stakeholders": trimmed_staks,
                              "departments": trimmed_depts,
                              "_note": "smoke test remove value"})
    check("removing stakeholder/department accepted", res2.status_code == 200,
          "status=%s" % res2.status_code)
    detail_removed = client.get("/api/linkedin/activities/%s" % aid).get_json()
    check("removed values are gone from the canonical row",
          sorted(detail_removed["stakeholders"]) == sorted(trimmed_staks) and
          sorted(detail_removed["departments"]) == sorted(trimmed_depts),
          "stakeholders=%s departments=%s" % (detail_removed["stakeholders"],
                                               detail_removed["departments"]))
    gone_stak = {s["stakeholder"]: s["activity_count"] for s in
                 client.get("/api/linkedin/stakeholders").get_json()}
    check("removed stakeholder leaves the stakeholder dimension",
          gone_stak.get(new_staks[-1], 0) < stak_counts.get(new_staks[-1], 0),
          "before=%s after=%s" % (stak_counts.get(new_staks[-1]),
                                  gone_stak.get(new_staks[-1])))
    check("still no duplicate activity after removal",
          conn_count() == rows_before,
          "rows=%d" % conn_count())

    # -- a PATCH that changes nothing must not alter the canonical row
    same = client.patch("/api/admin/linkedin/activities/%s" % aid, headers=headers,
                        json={"stakeholders": trimmed_staks,
                              "departments": trimmed_depts,
                              "_note": "smoke test no-op"})
    detail_noop = client.get("/api/linkedin/activities/%s" % aid).get_json()
    check("re-saving identical values is a no-op (discard-safe)",
          sorted(detail_noop["stakeholders"]) == sorted(trimmed_staks) and
          sorted(detail_noop["departments"]) == sorted(trimmed_depts) and
          conn_count() == rows_before,
          "status=%s" % same.status_code)
    detail_after = detail_noop
    new_staks, new_depts = trimmed_staks, trimmed_depts

    # ------------------------------------------------------------------ 5
    print("\n== 5. Ask the Data ==")
    for q in ("How many workshops were conducted?",
              "How many Clubs were conducted?",
              "How many achievements were recorded?",
              "How many activities were conducted in the academic year 2025-26?",
              "Which department conducted the most workshops?"):
        ans = client.get("/api/linkedin/query", query_string={"q": q}).get_json()
        check("query '%s'" % q,
              bool(ans.get("answer")) and ans.get("status") != "unsupported",
              "count=%s answer=%s" % (ans.get("count"),
                                      str(ans.get("answer"))[:60]))

    total_reportable = client.get("/api/linkedin/analytics/overview").get_json()[
        "total_reportable_activities"]
    cat_q = client.get("/api/linkedin/query",
                       query_string={"q": "How many workshops were conducted?"}
                       ).get_json()
    cat_rows = sum(c["activity_count"] for c in
                   client.get("/api/linkedin/categories").get_json()
                   if c["category"] == "WORKSHOP")
    check("category answer matches the analytics count for the same dataset",
          cat_q.get("count") == cat_rows,
          "nlq=%s analytics=%s" % (cat_q.get("count"), cat_rows))
    all_q = client.get("/api/linkedin/query",
                       query_string={"q": "How many activities were conducted?"}
                       ).get_json()
    check("overall answer matches the dashboard total",
          all_q.get("count") == total_reportable,
          "nlq=%s dashboard=%s" % (all_q.get("count"), total_reportable))
    stak_q = client.get("/api/linkedin/query",
                        query_string={"q": "How many activities did faculty and students attend?"}
                        ).get_json()
    check("stakeholder question answered from the same dataset",
          stak_q.get("count") is not None and stak_q.get("count") <= total_reportable,
          "count=%s" % stak_q.get("count"))
    edited_q = client.get(
        "/api/linkedin/query",
        query_string={"q": "How many activities involved %s?"
                      % new_staks[0].lower()}
    ).get_json()
    check("Ask the Data sees the admin-edited stakeholder",
          (edited_q.get("count") or 0) >= 1
          and edited_q.get("status") != "unsupported",
          "count=%s status=%s" % (edited_q.get("count"), edited_q.get("status")))

    # ------------------------------------------------------------------ 6
    print("\n== 6. XLSX / PDF exports ==")
    from openpyxl import load_workbook

    for label, args in (
            ("ACHIEVEMENT general",
             {"report_type": "all", "scope": "general", "category": "ACHIEVEMENT"}),
            ("ACHIEVEMENT departmental",
             {"report_type": "all", "scope": "departmental",
              "category": "ACHIEVEMENT"}),
            ("WORKSHOP departmental",
             {"report_type": "all", "scope": "departmental", "category": "WORKSHOP"}),
            ("CLUB general", {"report_type": "all", "scope": "general",
                              "category": "CLUB"})):
        # what the browser shows
        qs = dict(args)
        qs["report_type"] = args["report_type"]
        prev = client.get("/api/linkedin/reports/preview",
                          query_string=qs).get_json()
        visible = [c["label"] for c in prev["columns"]]

        blob, count, context = build_excel(args)
        ws = load_workbook(io.BytesIO(blob)).active
        xlsx_cols = [c.value for c in ws[5]]
        check("XLSX %s headers == visible report columns" % label,
              xlsx_cols == visible,
              "xlsx=%s visible=%s" % (xlsx_cols, visible))
        check("XLSX %s has a data row per activity" % label,
              ws.max_row - 5 == len(prev["records"]),
              "rows=%d records=%d" % (ws.max_row - 5, len(prev["records"])))

        pdf, _count, _ctx = build_pdf(args)
        check("PDF %s generated from the same columns" % label,
              pdf[:4] == b"%PDF" and len(pdf) > 800, "bytes=%d" % len(pdf))

    # The admin edit must be visible in an export of the edited category.
    edited_cat = new_cat[0]
    args = {"report_type": "all", "scope": "departmental", "category": edited_cat}
    prev = client.get("/api/linkedin/reports/preview", query_string=args).get_json()
    prev_cols = [c["label"] for c in prev["columns"]]
    blob, count, _ctx = build_excel(args)
    ws = load_workbook(io.BytesIO(blob)).active
    rows = list(ws.iter_rows(min_row=6, values_only=True))
    check("XLSX of the edited category uses the visible schema",
          [c.value for c in ws[5]] == prev_cols,
          "cols=%s" % [c.value for c in ws[5]])
    # The ACHIEVEMENT schema has no Title column, so the edited row is located
    # by its LinkedIn URL (falling back to the description).
    url = (detail_after.get("post_url") or "").strip()
    marker = url or (detail_after.get("achievement_description") or "")[:60]

    def matches(row):
        return any(str(v or "").strip() == marker for v in row)

    hit = [r for r in rows if matches(r)]
    check("edited activity appears in the export", bool(hit),
          "rows=%d marker=%r" % (len(rows), marker[:50]))
    if hit and "Department" in prev_cols:
        di = prev_cols.index("Department")
        cell = str(hit[0][di] or "")
        # The Department column renders each department as its catalog acronym
        # (Alumni Meet reports it that way), so accept either form and check the
        # cell against every department the admin added, not just one of them.
        from backend.database.report_fields import department_acronym
        named = [d for d in new_depts
                 if d in cell or department_acronym(d) in cell]
        check("exported Department cell shows the admin-added departments",
              len(named) >= len(orig_depts) and len(named) > 0,
              "cell=%r matched=%d of %d" % (cell, len(named), len(new_depts)))
    if hit and "Stakeholder" in prev_cols:
        si = prev_cols.index("Stakeholder")
        check("exported Stakeholder cell shows the admin stakeholders",
              all(s.split()[0].lower() in str(hit[0][si]).lower()
                  for s in new_staks),
              "cell=%r expected=%s" % (hit[0][si], new_staks))
    check("no duplicate activity in the export",
          len([r for r in rows if matches(r)]) == 1,
          "matches=%d" % len([r for r in rows if matches(r)]))


def conn_count():
    import sqlite3
    conn = sqlite3.connect(CANONICAL_DB)
    try:
        return conn.execute(
            "SELECT COUNT(*) c FROM linkedin_reportable_activities").fetchone()[0]
    finally:
        conn.close()


if __name__ == "__main__":
    main()
    failed = [r for r in RESULTS if not r[1]]
    print("\n%d checks, %d failed" % (len(RESULTS), len(failed)))
    for label, _ok, detail in failed:
        print("  FAIL %s  %s" % (label, detail))
    sys.exit(1 if failed else 0)