"""Real-data smoke test: exercise every LinkedIn surface against the live
reportable DB (no mocks, no fixtures).

Covers: Dashboard, Categories, Departments, Stakeholders, Reports preview/export,
Ask the Data, Admin review, Activity details, filters, and internal-field leakage.
"""
import atexit, hashlib, io, json, os, shutil, sys, tempfile
sys.path.insert(0, os.path.abspath('.'))

AY = '2026-27'
SMOKE_PW = "smoke-only-password"
# config.py reads these at import time, so the throwaway admin digest must be
# exported before the app package is imported. The repo intentionally keeps only
# a SHA-256 digest, so the real password is never available to this script.
os.environ.setdefault('ADMIN_USERNAME', 'shalini')
os.environ['ADMIN_PASSWORD_HASH'] = hashlib.sha256(SMOKE_PW.encode()).hexdigest()

from backend.app import create_app

NEWWB = 'Posts From June 2026 - September 2026.xlsx'
INTERNAL = ('description', 'category_candidates', 'department_candidates',
            'stakeholder_candidates', 'department_display', 'category_evidence',
            'department_evidence', 'stakeholder_evidence', 'evidence_score',
            'multi_label', 'flags', 'unclear_reason', 'reason', 'kind',
            'is_manually_validated', 'manual_overrides', 'validation_history',
            'staging_post_id', 'staging_candidate_id', 'source_sheet',
            'source_row', 'source_workbook', 'occurrence_count',
            'source_occurrence_ids', 'collected_at', 'resolved_via',
            'activity_urn_id', 'classification_status', 'review_status',
            'date_status', 'date_evidence', 'communication_type',
            'communication_evidence')

app = create_app()
app.config['TESTING'] = True
results = []

# The admin round trip below writes to the live databases. Snapshot them first so
# the script always leaves the real data byte-identical to how it found it.
LIVE_DBS = ['backend/database/linkedin_staging.db',
            'backend/database/linkedin_reportable.db']
_snapdir = tempfile.mkdtemp(prefix='linkedin_smoke_')
_snapshots = {p: os.path.join(_snapdir, os.path.basename(p)) for p in LIVE_DBS}
for _src, _dst in _snapshots.items():
    shutil.copy2(_src, _dst)


_restored = []


def restore_live_dbs():
    if _restored:
        return
    _restored.append(True)
    for src, dst in _snapshots.items():
        if os.path.exists(dst):
            shutil.copy2(dst, src)
    shutil.rmtree(_snapdir, ignore_errors=True)


atexit.register(restore_live_dbs)


def check(name, ok, detail=''):
    results.append((name, bool(ok), detail))
    print('  [%s] %-46s %s' % ('PASS' if ok else 'FAIL', name, detail))


def body(resp):
    """Return the full JSON payload (list endpoints expose `data` + totals)."""
    return resp.get_json()


def items_of(d):
    return d.get('data') or []


with app.test_client() as c:
    print('=' * 74)
    print('DASHBOARD / ACTIVITIES')
    print('=' * 74)
    r = c.get('/api/linkedin/activities?page_size=1')
    d = body(r)
    check('GET /api/linkedin/activities', r.status_code == 200 and d.get('total', 0) > 0,
          'total=%s' % d.get('total'))

    r = c.get('/api/linkedin/activities?academic_year=%s&page_size=1' % AY)
    d = body(r)
    check('activities filtered to AY %s' % AY, r.status_code == 200 and d.get('total', 0) > 0,
          'total=%s' % d.get('total'))

    # June-Sep 2026 records actually reachable through the public list
    r = c.get('/api/linkedin/activities?academic_year=%s&page_size=200' % AY)
    d = body(r)
    months = {}
    for a in items_of(d):
        m = (a.get('activity_date') or '')[:7]
        if m:
            months[m] = months.get(m, 0) + 1
    jun_sep = sum(v for k, v in months.items() if k in ('2026-06', '2026-07', '2026-08', '2026-09'))
    check('June-Sep 2026 records returned by public API', jun_sep > 0, 'months=%s' % months)

    sample = items_of(d)[0]
    check('public record has the 13 public fields',
          set(sample) == {'activity_id', 'title', 'summary', 'post_url', 'activity_date',
                          'academic_year', 'category', 'categories', 'department',
                          'departments', 'stakeholder', 'stakeholders', 'source'},
          sorted(sample))
    leaked = sorted(f for f in sample if f in INTERNAL)
    check('no internal fields leaked in list record', not leaked, str(leaked))
    check('raw LinkedIn paragraph not used as description',
          'description' not in sample and 'summary' in sample,
          'summary=%r' % str(sample.get('summary'))[:90])
    check('department shows a bare name (General for institution-wide)',
          sample['department'] == 'General' or isinstance(sample['department'], str),
          sample['department'])
    check('title/summary/date/AY/category/dept/stakeholder all populated',
          all(sample.get(k) for k in ('title', 'summary', 'activity_date', 'academic_year',
                                      'category', 'department', 'stakeholder')),
          'activity_id=%s' % sample['activity_id'])

    print()
    print('=' * 74)
    print('ACTIVITY DETAILS')
    print('=' * 74)
    aid = sample['activity_id']
    r = c.get('/api/linkedin/activities/%s' % aid)
    d = body(r)
    check('GET /api/linkedin/activities/<id>', r.status_code == 200 and d.get('activity_id') == aid,
          aid)
    check('detail leaks nothing internal',
          not sorted(f for f in d if f in INTERNAL), '')
    r = c.get('/api/linkedin/activities/LI-99999')
    check('unknown activity -> 404', r.status_code == 404, str(r.status_code))

    print()
    print('=' * 74)
    print('CATEGORIES / DEPARTMENTS / STAKEHOLDERS / YEARS')
    print('=' * 74)
    r = c.get('/api/linkedin/categories')
    cats = body(r)
    check('GET /api/linkedin/categories', r.status_code == 200 and len(cats) > 0,
          '%d categories' % len(cats))
    check('only the 24 known codes used',
          all(x['category'] in
              {'WORKSHOP', 'SEMINAR', 'CONFERENCE', 'SYMPOSIUM', 'GUEST_LECTURE', 'FDP',
               'STTP', 'HACKATHON', 'TECH_FEST', 'CULTURAL', 'SPORTS', 'NCC', 'NSS',
               'CLUB', 'OUTREACH', 'INDUSTRY', 'ACHIEVEMENT', 'PLACEMENT',
               'INTERNSHIP', 'RESEARCH', 'ALUMNI', 'ORIENTATION', 'CAMPUS', 'WEBINAR'}
              for x in cats), str(sorted(x['category'] for x in cats))[:120])

    r = c.get('/api/linkedin/departments')
    depts = body(r)
    check('GET /api/linkedin/departments', r.status_code == 200 and len(depts) > 0,
          '%d departments' % len(depts))
    check("'General' offered as an institution-wide bucket",
          any(x['department'] == 'General' for x in depts))
    check('department labels are plain names (no single/multiple labels)',
          all(not any(t in x['department'] for t in ('single', 'multiple', 'Multiple', 'Single'))
              for x in depts))

    r = c.get('/api/linkedin/stakeholders')
    staks = body(r)
    check('GET /api/linkedin/stakeholders', r.status_code == 200 and len(staks) > 0,
          '%d stakeholders' % len(staks))

    r = c.get('/api/linkedin/years')
    years = body(r)
    check('GET /api/linkedin/years', r.status_code == 200 and len(years) > 0,
          str({y['academic_year']: y['activity_count'] for y in years}))
    check('AY %s present' % AY, any(y['academic_year'] == AY for y in years))

    r = c.get('/api/linkedin/filters')
    f = body(r)
    check('GET /api/linkedin/filters', r.status_code == 200 and AY in f['years'],
          'years=%s' % f['years'])
    check('filter date_range now reaches Sep 2026',
          (f['date_range']['latest'] or '') >= '2026-09', str(f['date_range']))

    print()
    print('=' * 74)
    print('ANALYTICS OVERVIEW')
    print('=' * 74)
    r = c.get('/api/linkedin/analytics/overview')
    ov = body(r)
    total = ov['total_reportable_activities']
    check('GET overview', r.status_code == 200 and total > 0, 'total=%s' % total)
    g, dp = ov['general_departmental']['general'], ov['general_departmental']['departmental']
    check('General + Departmental reconcile to unique total', g + dp == total,
          '%d + %d = %d' % (g, dp, total))
    check('AY %s counted in overview' % AY,
          any(y['academic_year'] == AY and y['activity_count'] > 0
              for y in ov['activities_by_academic_year']))
    check('categories covered == 24', ov['categories_covered'] == 24, str(ov['categories_covered']))

    print()
    print('=' * 74)
    print('REPORTS (preview + export share the same dataset)')
    print('=' * 74)
    r = c.get('/api/linkedin/reports/preview?report_type=all&scope=departmental')
    pv = body(r)
    r2 = c.get('/api/linkedin/reports/preview?report_type=all&scope=departmental'
               '&academic_year=%s' % AY)
    pv_ay = body(r2)
    check('GET reports/preview', r.status_code == 200 and 'total' in pv, 'total=%s' % pv.get('total'))
    check('report preview honours AY %s' % AY, r2.status_code == 200 and pv_ay['total'] > 0,
          'total=%s' % pv_ay['total'])
    api_total = body(c.get('/api/linkedin/activities?academic_year=%s&page_size=1' % AY))['total']
    pv_gen = body(c.get('/api/linkedin/reports/preview?report_type=all&scope=general'
                        '&academic_year=%s' % AY))
    check('report previews (general + departmental) == activities API total',
          pv_gen['total'] + pv_ay['total'] == api_total,
          '%d + %d = %d vs %d' % (pv_gen['total'], pv_ay['total'],
                                   pv_gen['total'] + pv_ay['total'], api_total))
    check('report preview records are public-only',
          all(set(rec) == {'activity_id', 'title', 'summary', 'post_url', 'activity_date',
                           'academic_year', 'category', 'categories', 'department',
                           'departments', 'stakeholder', 'stakeholders', 'source'}
              for rec in (pv_ay.get('records') or [])[:20]),
          'keys=%s' % (sorted(pv_ay['records'][0]) if pv_ay.get('records') else 'no records'))
    r = c.get('/api/linkedin/reports/export?format=xlsx&academic_year=%s&report_type=all' % AY)
    check('GET reports/export (xlsx)', r.status_code == 200 and len(r.data) > 1000,
          '%d bytes' % len(r.data))
    r = c.get('/api/linkedin/reports/preview?report_type=bogus')
    check('invalid report_type rejected', r.status_code == 400, str(r.status_code))

    print()
    print('=' * 74)
    print('ASK THE DATA')
    print('=' * 74)
    for q in ('How many activities in academic year %s?' % AY,
              'How many %s activities in %s?' % ('Research', AY),
              'List departments for academic year %s' % AY):
        r = c.get('/api/linkedin/query', query_string={'q': q})
        d = body(r)
        check('query: %s' % q[:52], r.status_code == 200 and d.get('answer'),
              'count=%s answer=%s' % (d.get('count'), str(d.get('answer'))[:70]))
    r = c.get('/api/linkedin/query', query_string={'q': ''})
    check('empty question rejected', r.status_code == 400, str(r.status_code))
    r = c.get('/api/linkedin/query', query_string={'q': 'x' * 600})
    check('overlong question rejected', r.status_code == 400, str(r.status_code))
    r = c.get('/api/linkedin/query?q=How many activities in academic year %s?' % AY)
    d = body(r)
    api_total = body(c.get('/api/linkedin/activities?academic_year=%s&page_size=1' % AY))['total']
    check('Ask the Data count == reporting dataset count', d.get('count') == api_total,
          '%s == %s' % (d.get('count'), api_total))
    r = c.get('/api/linkedin/query/export?q=How many activities in academic year %s?&format=xlsx' % AY)
    check('query export xlsx', r.status_code == 200 and len(r.data) > 500, '%d bytes' % len(r.data))

    print()
    print('=' * 74)
    print('ADMIN (queue / records / detail / overrides)')
    print('=' * 74)
    r = c.post('/api/admin/login', json={'username': 'shalini', 'password': SMOKE_PW})
    token = (body(r) or {}).get('token') if r.status_code == 200 else None
    check('admin login', r.status_code == 200 and bool(token), 'status=%s token=%s' % (r.status_code, bool(token)))
    check('login response carries no plaintext password',
          SMOKE_PW not in json.dumps(body(r) or {}), '')
    if token:
        c.environ_base['HTTP_AUTHORIZATION'] = 'Bearer %s' % token
    r = c.get('/api/admin/linkedin/summary')
    adm = body(r)
    check('GET admin/linkedin/summary', r.status_code == 200 and adm, str(r.status_code))
    check('REVIEW_REQUIRED present in admin layer',
          adm.get('total_review_required', 0) > 0, 'review_required=%s' % adm.get('total_review_required'))
    check('NON_ACTIVITY tracked in admin layer',
          adm.get('total_non_activities', 0) > 0, 'non_activities=%s' % adm.get('total_non_activities'))
    all_total = body(c.get('/api/linkedin/activities?page_size=1'))['total']
    check('admin summary totals match the reportable DB',
          adm.get('total_reportable_activities') == all_total
          and adm.get('total_canonical_posts') == 1747,
          'reportable=%s/%s canonical=%s/1747' % (adm.get('total_reportable_activities'),
                                                  all_total,
                                                  adm.get('total_canonical_posts')))

    def wb_of(rec):
        p = rec.get('provenance')
        return p.get('source_workbook') if isinstance(p, dict) else None

    def page_all(status):
        """Collect every admin record for a status, following pagination."""
        out, page = [], 1
        while True:
            rr = c.get('/api/admin/linkedin/activities?status=%s&page=%d&page_size=200'
                       % (status, page))
            chunk = items_of(body(rr))
            out.extend(chunk)
            if len(chunk) < 200:
                return out
            page += 1

    r = c.get('/api/admin/linkedin/review-queue?status=REVIEW_REQUIRED&page_size=5')
    q = body(r)
    check('GET admin/linkedin/review-queue (REVIEW_REQUIRED)',
          r.status_code == 200 and q.get('total', 0) > 0, 'total=%s' % q.get('total'))
    check('review-queue total == admin summary review_required',
          q.get('total') == adm.get('total_review_required'),
          '%s == %s' % (q.get('total'), adm.get('total_review_required')))

    rev = page_all('REVIEW_REQUIRED')
    rep_rows = page_all('REPORTABLE')
    non_rows = page_all('NON_ACTIVITY')
    new_rev = [x for x in rev if wb_of(x) == NEWWB]
    new_rep = [x for x in rep_rows if wb_of(x) == NEWWB]
    new_non = [x for x in non_rows if wb_of(x) == NEWWB]
    check('new-source rows reachable in the admin review queue', len(new_rev) == 23,
          '%d of %d review-required' % (len(new_rev), len(rev)))
    check('new-source rows reachable in admin reportable list', len(new_rep) == 171,
          '%d of %d reportable' % (len(new_rep), len(rep_rows)))
    check('new-source rows reachable in admin non-activity list', len(new_non) == 9,
          '%d of %d non-activity' % (len(new_non), len(non_rows)))
    check('admin layer covers every canonical post',
          len(rev) + len(rep_rows) + len(non_rows) == adm.get('total_canonical_posts'),
          '%d+%d+%d=%s' % (len(rev), len(rep_rows), len(non_rows),
                           adm.get('total_canonical_posts')))

    if items_of(q):
        row = items_of(q)[0]
        r = c.get('/api/admin/linkedin/activities/%s' % row['activity_id'])
        rec = body(r)
        check('GET admin/linkedin/activities/<id> (rich internal view)', r.status_code == 200,
              row['activity_id'])
        check('admin record exposes internal evidence (expected here)',
              'category_evidence' in rec and 'evidence_score' in rec)
        check('admin record exposes provenance', isinstance(rec.get('provenance'), dict)
              and 'source_workbook' in rec['provenance'],
              'wb=%s' % rec['provenance'].get('source_workbook'))
        r = c.get('/api/admin/linkedin/options')
        check('GET admin/linkedin/options', r.status_code == 200, str(r.status_code))
        r = c.get('/api/admin/linkedin/activities/%s' % row['activity_id'])
        check('detail endpoint requires auth (unauthenticated read rejected)',
              c.get('/api/admin/linkedin/activities/%s' % row['activity_id'],
                    headers={'Authorization': 'Bearer bogus-token'}).status_code == 401, '')

    # manual override + publish round trip on a NEW post, then revert
    print()
    print('  -- manual override round trip on a new-source record --')
    cand = new_rev[0] if new_rev else None
    if cand:
        target = cand['activity_id']
        r = c.get('/api/admin/linkedin/activities/%s' % target)
        before_rec = body(r)
        check('new record starts with no manual edits',
              not before_rec.get('is_manually_validated')
              and not (before_rec.get('validation_history') or []),
              'validated=%s history=%d' % (before_rec.get('is_manually_validated'),
                                           len(before_rec.get('validation_history') or [])))
        r = c.patch('/api/admin/linkedin/activities/%s' % target,
                    json={'review_status': 'APPROVED', 'categories': ['CAMPUS']},
                    headers={'X-Reviewer': 'smoke-test'})
        check('PATCH admin override on new post', r.status_code == 200,
              '%s -> %s' % (target, r.status_code))
        r = c.get('/api/admin/linkedin/activities/%s' % target)
        after_rec = body(r)
        check('override applied', after_rec.get('review_status') == 'APPROVED'
              and after_rec.get('categories') == ['CAMPUS'],
              '%s %s' % (after_rec.get('review_status'), after_rec.get('categories')))
        check('validation_history recorded and attributed to the signed-in admin',
              bool(after_rec.get('validation_history'))
              and after_rec['validation_history'][-1].get('by') == 'shalini',
              str(after_rec.get('validation_history'))[:120])
        # revert to the classifier's own values
        r = c.patch('/api/admin/linkedin/activities/%s' % target,
                    json={'review_status': 'NEEDS_REVIEW',
                          'categories': before_rec.get('category_candidates')},
                    headers={'X-Reviewer': 'smoke-test-revert'})
        rr = body(r)
        check('revert applied', rr.get('review_status') == 'NEEDS_REVIEW',
              str(rr.get('review_status')))
    else:
        check('found a new-source REVIEW_REQUIRED record to test overrides', False, 'none found')

    print()
    print('=' * 74)
    print('PAGINATION / SORT / ERROR HANDLING')
    print('=' * 74)
    r = c.get('/api/linkedin/activities?page=2&page_size=10')
    d = body(r)
    check('pagination page 2', r.status_code == 200 and d['pagination']['page'] == 2,
          'page=%s' % d['pagination']['page'])
    r = c.get('/api/linkedin/activities?sort=bogus')
    check('invalid sort rejected', r.status_code == 400, str(r.status_code))
    r = c.get('/api/linkedin/activities?order=sideways')
    check('invalid order rejected', r.status_code == 400, str(r.status_code))
    r = c.get('/api/linkedin/activities?department=Not%20A%20Department')
    d = body(r)
    check('unknown department rejected with a clear 400 (not a crash/500)',
          r.status_code == 400 and 'error' in d, '%s %s' % (r.status_code, d))

failed = [x for x in results if not x[1]]
print()
print('=' * 74)
print('SMOKE TEST: %d checks, %d passed, %d failed'
      % (len(results), len(results) - len(failed), len(failed)))
for n, _, d in failed:
    print('  FAILED: %s  %s' % (n, d))
print('=' * 74)
restore_live_dbs()
print('Live staging/reportable DBs restored to their pre-test state.')
sys.exit(1 if failed else 0)
