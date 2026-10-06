"""AY 2026-27 validation + cross-layer consistency checks (read-only)."""
import json, os, sys
from collections import Counter
sys.path.insert(0, os.path.abspath('.'))
from backend.database import linkedin_reportable as rep

AY = '2026-27'
NEWWB = 'Posts From June 2026 - September 2026.xlsx'
conn = rep.get_reportable_connection()
out = {}


def one(sql, p=()):
    return conn.execute(sql, p).fetchone()[0]


def many(sql, p=()):
    return conn.execute(sql, p).fetchall()


print('=' * 72)
print('AY %s VALIDATION' % AY)
print('=' * 72)

out['total_rows'] = one("SELECT COUNT(*) FROM linkedin_reportable_activities")
out['dated_total'] = one(
    "SELECT COUNT(*) FROM linkedin_reportable_activities WHERE date_status='dated'")
out['ay_2026_27_dated_all_status'] = one(
    "SELECT COUNT(*) FROM linkedin_reportable_activities "
    "WHERE academic_year=? AND date_status='dated'", (AY,))
out['ay_2026_27_reportable'] = one(
    "SELECT COUNT(*) FROM linkedin_reportable_activities "
    "WHERE academic_year=? AND reportable_status='REPORTABLE'", (AY,))
out['ay_2026_27_non_activity'] = one(
    "SELECT COUNT(*) FROM linkedin_reportable_activities "
    "WHERE academic_year=? AND reportable_status='NON_ACTIVITY'", (AY,))
out['ay_2026_27_review_required'] = one(
    "SELECT COUNT(*) FROM linkedin_reportable_activities "
    "WHERE academic_year=? AND reportable_status='REVIEW_REQUIRED'", (AY,))
for k in ('total_rows', 'dated_total', 'ay_2026_27_dated_all_status', 'ay_2026_27_reportable',
          'ay_2026_27_non_activity', 'ay_2026_27_review_required'):
    print('  %-34s %d' % (k, out[k]))

# reconcile: dated AY rows == reportable + non_activity + review_required
tot = (out['ay_2026_27_reportable'] + out['ay_2026_27_non_activity']
       + out['ay_2026_27_review_required'])
print('  reconcile (reportable+non_act+review) = %d  -> %s'
      % (tot, 'OK' if tot == out['ay_2026_27_dated_all_status'] else 'MISMATCH'))
out['ay_2026_27_reconciles'] = (tot == out['ay_2026_27_dated_all_status'])

# NEW-source-only AY figures
w = ' AND source_workbook=?'
out['new_source_reportable'] = one(
    "SELECT COUNT(*) FROM linkedin_reportable_activities "
    "WHERE source_workbook=? AND reportable_status='REPORTABLE'", (NEWWB,))
out['new_source_ay_2026_27_reportable'] = one(
    "SELECT COUNT(*) FROM linkedin_reportable_activities WHERE source_workbook=? "
    "AND academic_year=? AND reportable_status='REPORTABLE'", (NEWWB, AY))
out['new_source_non_activity'] = one(
    "SELECT COUNT(*) FROM linkedin_reportable_activities "
    "WHERE source_workbook=? AND reportable_status='NON_ACTIVITY'", (NEWWB,))
out['new_source_review_required'] = one(
    "SELECT COUNT(*) FROM linkedin_reportable_activities "
    "WHERE source_workbook=? AND reportable_status='REVIEW_REQUIRED'", (NEWWB,))
out['new_source_undated'] = one(
    "SELECT COUNT(*) FROM linkedin_reportable_activities "
    "WHERE source_workbook=? AND date_status<>'dated'", (NEWWB,))
print()
print('  NEW SOURCE ONLY:')
for k in ('new_source_reportable', 'new_source_ay_2026_27_reportable',
          'new_source_non_activity', 'new_source_review_required', 'new_source_undated'):
    print('    %-34s %d' % (k, out[k]))

print()
print('--- AY 2026-27 month coverage (reportable, new source) ---')
months = {}
for m in ('2026-06', '2026-07', '2026-08', '2026-09'):
    months[m] = one(
        "SELECT COUNT(*) FROM linkedin_reportable_activities WHERE academic_year=? "
        "AND source_workbook=? AND reportable_status='REPORTABLE' AND substr(activity_date,1,7)=?",
        (AY, NEWWB, m))
    print('    %s : %d' % (m, months[m]))
out['ay_2026_27_new_source_months'] = months
out['ay_2026_27_new_source_jun_sep_total'] = sum(months.values())

print()
print('--- AY 2026-27 category distribution (REPORTABLE) ---')
cats = [(r['category_code'], r['n']) for r in many(
    "SELECT c.category_code, COUNT(*) n FROM linkedin_activity_categories c "
    "JOIN linkedin_reportable_activities r ON r.activity_id=c.activity_id "
    "WHERE r.academic_year=? AND r.reportable_status='REPORTABLE' "
    "GROUP BY 1 ORDER BY n DESC", (AY,))]
out['ay_2026_27_categories'] = dict(cats)
for c, n in cats:
    print('    %-16s %d' % (c, n))

print()
print('--- AY 2026-27 department distribution (REPORTABLE) ---')
depts = [(r['department'], r['n']) for r in many(
    "SELECT d.department, COUNT(*) n FROM linkedin_activity_departments d "
    "JOIN linkedin_reportable_activities r ON r.activity_id=d.activity_id "
    "WHERE r.academic_year=? AND r.reportable_status='REPORTABLE' "
    "GROUP BY 1 ORDER BY n DESC", (AY,))]
out['ay_2026_27_departments'] = dict(depts)
for d, n in depts:
    print('    %-46s %d' % (d, n))

print()
print('--- AY 2026-27 stakeholder distribution (REPORTABLE) ---')
staks = [(r['stakeholder'], r['n']) for r in many(
    "SELECT s.stakeholder, COUNT(*) n FROM linkedin_activity_stakeholders s "
    "JOIN linkedin_reportable_activities r ON r.activity_id=s.activity_id "
    "WHERE r.academic_year=? AND r.reportable_status='REPORTABLE' "
    "GROUP BY 1 ORDER BY n DESC", (AY,))]
out['ay_2026_27_stakeholders'] = dict(staks)
for s, n in staks:
    print('    %-28s %d' % (s, n))

print()
print('=' * 72)
print('CONSISTENCY CHECKS')
print('=' * 72)
checks = []


def check(name, ok, detail=''):
    checks.append({'check': name, 'pass': bool(ok), 'detail': detail})
    print('  [%s] %-52s %s' % ('PASS' if ok else 'FAIL', name, detail))


# unique total stable under filters
base = rep.count_reportable(conn, {})
check('count_reportable() == status=REPORTABLE rows',
      base == out['ay_2026_27_reportable'] or base == one(
          "SELECT COUNT(*) FROM linkedin_reportable_activities WHERE reportable_status='REPORTABLE'"),
      'total=%d' % base)
rep_rows = one("SELECT COUNT(*) FROM linkedin_reportable_activities WHERE reportable_status='REPORTABLE'")
check('unique REPORTABLE total == API count', base == rep_rows, '%d == %d' % (base, rep_rows))
for y in ('2024-25', '2025-26', AY, '2023-24'):
    n = rep.count_reportable(conn, {'academic_year': y})
    check('year filter %s total matches grouped count' % y,
          n == one("SELECT COUNT(*) FROM linkedin_reportable_activities "
                   "WHERE reportable_status='REPORTABLE' AND academic_year=?", (y,)), str(n))

# normalized tables reconcile with the JSON lists
bad = one("""SELECT COUNT(*) FROM linkedin_reportable_activities r
            WHERE r.reportable_status='REPORTABLE' AND (
              (SELECT COUNT(*) FROM linkedin_activity_categories c WHERE c.activity_id=r.activity_id)
              != json_array_length(r.categories)
              OR (SELECT COUNT(*) FROM linkedin_activity_departments d WHERE d.activity_id=r.activity_id)
              != json_array_length(r.departments)
              OR (SELECT COUNT(*) FROM linkedin_activity_stakeholders s WHERE s.activity_id=r.activity_id)
              != json_array_length(r.stakeholders))""")
check('normalized tables == stored JSON lists', bad == 0, '%d mismatched rows' % bad)
leak = one("""SELECT COUNT(*) FROM linkedin_activity_categories c
             LEFT JOIN linkedin_reportable_activities r ON r.activity_id=c.activity_id
             WHERE r.activity_id IS NULL OR r.reportable_status<>'REPORTABLE'""")
check('normalized tables contain REPORTABLE only', leak == 0, '%d leaks' % leak)

# General + departmental reconcile
gen = rep.count_reportable(conn, {'scope': 'general'})
dep = rep.count_reportable(conn, {'scope': 'departmental'})
check('General + Departmental == unique total', gen + dep == base,
      '%d + %d = %d vs %d' % (gen, dep, gen + dep, base))
ov = rep.analytics_overview(conn, {})
check('overview.general_departmental matches', ov['general_departmental'] ==
      {'general': gen, 'departmental': dep}, str(ov['general_departmental']))
check('overview total == count_reportable',
      ov['total_reportable_activities'] == base, str(ov['total_reportable_activities']))
check('overview yearly total == unique total',
      sum(r['activity_count'] for r in ov['activities_by_academic_year']) +
      one("SELECT COUNT(*) FROM linkedin_reportable_activities "
          "WHERE reportable_status='REPORTABLE' AND academic_year IS NULL") == base,
      'dated+undated')
check('yearly distribution matches',
      {r['academic_year']: r['activity_count'] for r in rep.analytics_yearly(conn, {})} ==
      {r['academic_year']: r['n'] for r in many(
          "SELECT academic_year, COUNT(*) n FROM linkedin_reportable_activities "
          "WHERE reportable_status='REPORTABLE' AND academic_year IS NOT NULL "
          "GROUP BY 1 ORDER BY 1")})
check('category distribution matches',
      {r['category']: r['activity_count'] for r in rep.analytics_categories(conn, {})} ==
      {r['category_code']: r['n'] for r in many(
          "SELECT c.category_code, COUNT(*) n FROM linkedin_activity_categories c "
          "JOIN linkedin_reportable_activities r ON r.activity_id=c.activity_id "
          "WHERE r.reportable_status='REPORTABLE' GROUP BY 1")})
check('department distribution matches',
      {r['department']: r['activity_count'] for r in rep.analytics_departments(conn, {})} ==
      {r['department']: r['n'] for r in many(
          "SELECT d.department, COUNT(*) n FROM linkedin_activity_departments d "
          "JOIN linkedin_reportable_activities r ON r.activity_id=d.activity_id "
          "WHERE r.reportable_status='REPORTABLE' GROUP BY 1")})
check('stakeholder distribution matches',
      {r['stakeholder']: r['activity_count'] for r in rep.analytics_stakeholders(conn, {})} ==
      {r['stakeholder']: r['n'] for r in many(
          "SELECT s.stakeholder, COUNT(*) n FROM linkedin_activity_stakeholders s "
          "JOIN linkedin_reportable_activities r ON r.activity_id=s.activity_id "
          "WHERE r.reportable_status='REPORTABLE' GROUP BY 1")})

# taxonomies unchanged
check('24 categories only (no new codes)',
      not one("SELECT COUNT(DISTINCT category_code) FROM linkedin_activity_categories "
              "WHERE category_code NOT IN (%s)"
              % ",".join("'%s'" % c for c in sorted(rep.FINAL_CATEGORY_CODES))),
      '%d codes in use' % one("SELECT COUNT(DISTINCT category_code) FROM linkedin_activity_categories"))
check('24-category vocabulary intact',
      rep.FINAL_CATEGORY_CODES == frozenset(rep.CATEGORY_PATTERNS)
      and len(rep.FINAL_CATEGORY_CODES) == 24,
      '%d codes' % len(rep.FINAL_CATEGORY_CODES))
check('no invalid departments', not one(
    "SELECT COUNT(*) FROM linkedin_activity_departments WHERE department NOT IN (%s)"
    % ",".join("'%s'" % d.replace("'", "''") for d in sorted(rep.FINAL_DEPARTMENTS))))
check('no invalid stakeholders', not one(
    "SELECT COUNT(*) FROM linkedin_activity_stakeholders WHERE stakeholder NOT IN (%s)"
    % ",".join("'%s'" % s.replace("'", "''") for s in sorted(rep.FINAL_STAKEHOLDERS))))

# duplicates
check('duplicate canonical posts (activity_id) = 0', one(
    "SELECT COUNT(*) FROM (SELECT activity_id FROM linkedin_reportable_activities "
    "GROUP BY 1 HAVING COUNT(*)>1)") == 0)
check('duplicate canonical posts (staging_post_id) = 0', one(
    "SELECT COUNT(*) FROM (SELECT staging_post_id FROM linkedin_reportable_activities "
    "GROUP BY 1 HAVING COUNT(*)>1)") == 0)
check('duplicate post_url = 0', one(
    "SELECT COUNT(*) FROM (SELECT post_url FROM linkedin_reportable_activities "
    "WHERE post_url IS NOT NULL GROUP BY 1 HAVING COUNT(*)>1)") == 0)
check('duplicate reportable titles+dates = 0 (new source)', one(
    "SELECT COUNT(*) FROM (SELECT title, activity_date FROM linkedin_reportable_activities "
    "WHERE source_workbook=? AND reportable_status='REPORTABLE' "
    "GROUP BY 1,2 HAVING COUNT(*)>1)", (NEWWB,)) == 0)

# traceability
check('every new reportable row traceable to new source',
      one("SELECT COUNT(*) FROM linkedin_reportable_activities WHERE source_workbook=? "
          "AND source_sheet='All posts' AND source_row IS NOT NULL", (NEWWB,)) ==
      out['new_source_reportable'] + out['new_source_non_activity']
      + out['new_source_review_required'])
# cross-database checks read staging through its own connection
stg = rep._ro_staging(None)
check('every staging post has a reportable row',
      stg.execute("SELECT COUNT(*) FROM linkedin_posts").fetchone()[0] == out['total_rows'],
      '%d staging posts vs %d reportable rows' % (
          stg.execute("SELECT COUNT(*) FROM linkedin_posts").fetchone()[0], out['total_rows']))
check('no reportable row without a staging candidate',
      stg.execute("SELECT COUNT(*) FROM linkedin_activity_candidates").fetchone()[0]
      == out['total_rows'])
stg.close()
check('NON_ACTIVITY excluded from public analytics',
      one("SELECT COUNT(*) FROM linkedin_activity_categories c JOIN linkedin_reportable_activities r "
          "ON r.activity_id=c.activity_id WHERE r.reportable_status='NON_ACTIVITY'") == 0)
check('REVIEW_REQUIRED retained in admin layer',
      one("SELECT COUNT(*) FROM linkedin_reportable_activities "
          "WHERE reportable_status='REVIEW_REQUIRED'") >= 228,
      '%d rows awaiting review (>= the 228 pre-migration)' % one(
          "SELECT COUNT(*) FROM linkedin_reportable_activities "
          "WHERE reportable_status='REVIEW_REQUIRED'"))
check('rows flagged for review carry no primary category',
      one("SELECT COUNT(*) FROM linkedin_reportable_activities "
          "WHERE validation_history LIKE '%migration:single_category_20261002%' "
          "AND reportable_status IN ('REVIEW_REQUIRED','NON_ACTIVITY') "
          "AND categories<>'[]'") == 0,
      '%d migration-flagged rows, none left with a forced category' % one(
          "SELECT COUNT(*) FROM linkedin_reportable_activities "
          "WHERE validation_history LIKE '%migration:single_category_20261002%' "
          "AND reportable_status IN ('REVIEW_REQUIRED','NON_ACTIVITY')"))
check('REVIEW_REQUIRED excluded from public analytics',
      one("SELECT COUNT(*) FROM linkedin_activity_categories c JOIN linkedin_reportable_activities r "
          "ON r.activity_id=c.activity_id WHERE r.reportable_status='REVIEW_REQUIRED'") == 0)
check('manual overrides intact', one(
    "SELECT COUNT(*) FROM linkedin_reportable_activities "
    "WHERE is_manually_validated=1") == 16)
check('approved records intact', one(
    "SELECT COUNT(*) FROM linkedin_reportable_activities "
    "WHERE review_status='APPROVED'") == 13)
check('historical sheets unchanged',
      {('%s | %s' % (r['source_workbook'], r['source_sheet'])): r['n'] for r in many(
          "SELECT source_workbook, source_sheet, COUNT(*) n FROM linkedin_reportable_activities "
          "WHERE source_workbook<>'%s' GROUP BY 1,2" % NEWWB)} == {
          'merged-workbook.xlsx | April 2024 - June 2025': 532,
          'merged-workbook.xlsx | Jan - Sep 2025': 293,
          'merged-workbook.xlsx | June 2025-June 2026': 718,
          'merged-workbook.xlsx | Sep to Dec 2025': 1})
check('no invented dates (activity_date implies dated)',
      one("SELECT COUNT(*) FROM linkedin_reportable_activities "
          "WHERE activity_date IS NOT NULL AND date_status<>'dated'") == 0)
# A non-dated row may carry an academic_year ONLY via a documented admin
# override (8 such historical records exist and must stay untouched).
offender = one(
    "SELECT COUNT(*) FROM linkedin_reportable_activities "
    "WHERE academic_year IS NOT NULL AND date_status<>'dated' "
    "AND (manual_overrides IS NULL OR manual_overrides NOT LIKE '%academic_year%')")
check('academic_year on non-dated rows only via manual override', offender == 0,
      '%d undocumented rows (8 documented overrides expected)' % offender)
check('no NEW row has an undocumented academic_year',
      one("SELECT COUNT(*) FROM linkedin_reportable_activities WHERE source_workbook=? "
          "AND academic_year IS NOT NULL AND date_status<>'dated'", (NEWWB,)) == 0)
check('AY 2026-27 present in availability/years filter',
      AY in rep.availability(conn)['years'], str(rep.availability(conn)['years']))
check('General present as department display value',
      one("SELECT COUNT(*) FROM linkedin_activity_departments WHERE department='General'") > 0)

out['checks'] = checks
out['checks_failed'] = [c for c in checks if not c['pass']]

print()
print('TOTAL CHECKS: %d   PASSED: %d   FAILED: %d'
      % (len(checks), sum(1 for c in checks if c['pass']), len(out['checks_failed'])))
for c in out['checks_failed']:
    print('  FAILED:', c['check'], c['detail'])

OUT_PATH = 'data/audit/linkedin_reportable_validation.json'
with open(OUT_PATH, 'w', encoding='utf-8') as f:
    json.dump(out, f, indent=2, sort_keys=True, default=str)
print('\nwritten %s' % OUT_PATH)
conn.close()
