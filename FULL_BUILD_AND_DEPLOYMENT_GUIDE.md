# Full Build & Free Deployment Guide
## NLP-Based Institutional Activity Intelligence and Evaluation System
### Case Study: Thiagarajar College of Engineering (TCE), Madurai

This is the complete phase-by-phase build plan for the project, plus a
100%-free deployment path at the end. It follows the same 14-phase order
already agreed for the project. **Do not skip ahead** — each phase should
be built, tested, and verified before the next one starts (see Phase 0/1
work already completed).

---

## How to use this document

- Work top to bottom, one phase at a time.
- Every phase lists: **Goal → Tools (all free) → Steps → What to test → Done-when**.
- "Free" means: no paid API keys, no paid hosting tier, no paid software license.
- Where a phase needs manual verification against the real TCE website (dates,
  URLs, department names), that is called out explicitly — never invent these.

---

## PHASE 0 — Project Inspection *(done)*

**Goal:** Confirm the environment and starting state before writing code.

- Check Python (3.10+), Node.js (18+), pip, npm are installed.
- Confirm no old project files exist, or inventory what does.
- Produce a short status report before building anything.

**Done when:** you have a written summary of what exists vs. what's missing.

---

## PHASE 1 — Database + Source Architecture *(done)*

**Goal:** Build the schema everything else plugs into.

**Tools:** Python 3, `sqlite3` (built into Python, free), `pytest`.

**Steps:**
1. Design tables: `institutional_activities`, `activity_sources`,
   `activity_departments`, `activity_categories`, `activity_stakeholders`,
   `activity_keywords`, `activity_entities`, `academic_years`, `departments`,
   `categories`, `stakeholders`, `classification_methods`, `source_registry`,
   `collection_runs`, `collection_errors`, `duplicate_candidates`,
   `linkedin_matches`, `review_queue`, `review_history`.
2. Write `backend/database/schema.sql` with all `CREATE TABLE` statements,
   foreign keys, and `CHECK` constraints (e.g. confidence between 0–1).
3. Write `backend/database/init_db.py` to build the `.db` file from the schema.
4. Write `backend/database/seed_reference_data.py` to insert ONLY fixed lookup
   data (5 academic years, 14 departments, 24 categories, 8 stakeholders,
   classification methods, starter source registry). **No activity records.**
5. Write `tests/test_database.py` covering: all tables exist, seed counts are
   correct, foreign keys are enforced, check constraints work, zero activities
   exist yet.

**Test:** `python -m pytest tests/test_database.py -v` → all pass.

**Done when:** database builds cleanly and every test passes with zero
fabricated activity data in the DB.

---

## PHASE 2 — Small TCE Website Collection Test

**Goal:** Prove you can legitimately collect a *small, real* sample from
`tce.edu` before scaling up.

**Tools:** `requests`, `beautifulsoup4`, `lxml` (all free, pip-installable).

**Steps:**
1. **Manually browse** `https://www.tce.edu` and note the real URLs for:
   Events, Academics, Departments, Sports, NCC, NSS, Clubs, Achievements,
   Outreach, and any PDF/newsletter pages. Update `source_registry` rows
   with the *actual* confirmed URLs (the ones seeded in Phase 1 are
   placeholders — verify every one).
2. Check `https://www.tce.edu/robots.txt` and respect it.
3. Write `backend/collectors/base_collector.py`: a shared base class handling
   — request headers/User-Agent, delay between requests (e.g. 2 seconds),
   retries on failure, logging, and writing raw HTML/text to `data/raw/`.
4. Write **one** collector first, e.g. `tce_events_collector.py`, that:
   - Fetches the Events listing page.
   - Extracts title, date, URL, raw text for each item found.
   - Saves raw output to `data/raw/events/` as JSON files (timestamped).
   - Logs a row into `collection_runs` (pages processed, raw records,
     errors) and `collection_errors` for any failures.
5. Run it on a **small sample only** (e.g. first page / first 10 items).

**Test:** Manually open 3–5 of the saved raw records and confirm the title,
date, and URL genuinely match what's on the live TCE page.

**Done when:** you have a small set of real, verifiable raw records saved to
disk with source URLs and timestamps — not fabricated.

> ⚠️ **Important constraint:** Any sandboxed AI coding tool (like a locked-down
> Claude container) usually can't reach external domains such as `tce.edu`.
> Run collectors from your own laptop or a normal cloud VM with open internet.

---

## PHASE 3 — Cleaning, Validation, Deduplication

**Goal:** Turn messy raw scraped text into clean, structured, non-duplicated rows.

**Tools:** `pandas`, Python's built-in `re` and `unicodedata`, `rapidfuzz`
(free, pip-installable) for fuzzy string matching.

**Steps:**
1. `backend/database/cleaner.py`: strip leftover HTML tags, normalize
   whitespace/unicode/punctuation, normalize dates into `YYYY-MM-DD`.
2. `backend/database/normalizer.py`: produce `normalized_title` (lowercase,
   punctuation-stripped) for every record — used for deduplication and search.
3. `backend/database/validator.py`: flag invalid records (no title, unparseable
   date, empty content) — **never silently delete**, log to `collection_errors`
   or a "needs review" flag instead.
4. `backend/database/deduplicator.py`: compare records pairwise using
   normalized title + date + department + fuzzy title similarity
   (`rapidfuzz.fuzz.ratio`). Insert high-confidence matches into
   `duplicate_candidates` with `status='Auto-Merged'`, ambiguous ones as
   `status='Pending'` for human review.
5. Load validated, deduplicated records into `institutional_activities`
   and `activity_sources`.

**Test:** Write `tests/test_cleaning.py` and `tests/test_deduplication.py`
with a handful of known sample inputs and expected cleaned/deduped outputs.

**Done when:** raw → clean → deduplicated pipeline runs on your Phase 2
sample and produces sensible, inspectable results.

---

## PHASE 4 — Information Extraction

**Goal:** Pull structured fields (venue, organizer, resource person, people,
organizations, dates, awards, etc.) out of free-text activity descriptions.

**Tools:** `spacy` (free, open-source) + `en_core_web_sm` model (free
download), `re` for regex patterns, a hand-built dictionary of known TCE
department/programme names for exact/fuzzy matching.

**Steps:**
1. `pip install spacy && python -m spacy download en_core_web_sm`
2. `backend/nlp/extractors.py`:
   - Regex/rule patterns for dates, venues ("held at...", "venue:"),
     resource persons ("resource person:", "chief guest:").
   - spaCy NER for `PERSON` and `ORG` entities.
   - Dictionary/fuzzy match against your department name list (with aliases)
     to detect department mentions.
3. Store results in `activity_entities` (with `entity_type`, `entity_text`,
   `confidence`, `extraction_method_id`) and `activity_keywords`.
4. Anything not confidently extracted → `NULL`/`Unknown`, never guessed.

**Test:** `tests/test_extraction.py` — feed 10–15 sample activity texts you've
manually read, compare extracted fields against what you expect.

**Done when:** entity/keyword extraction runs on your dataset and spot-checks
correctly on manually reviewed samples.

---

## PHASE 5 — NLP Classification & Model Comparison

**Goal:** Multi-label categorize each activity into the 24 categories, and
compare model choices instead of assuming one.

**Tools:** `scikit-learn` (free) — `TfidfVectorizer`, `LogisticRegression`,
`LinearSVC`, `MultinomialNB`, `OneVsRestClassifier`, `MultiLabelBinarizer`.

**Steps:**
1. Manually label a subset of ~150–300 collected activities with their
   correct categories (your ground-truth set — reuse it later in Phase 13).
2. `backend/nlp/preprocess.py`: tokenize, remove stopwords, lemmatize
   (spaCy), build TF-IDF features (unigrams + bigrams).
3. `backend/nlp/train_models.py`: train and compare, on the same
   train/test split:
   - Rule-based keyword baseline
   - TF-IDF + Logistic Regression (One-vs-Rest)
   - TF-IDF + Linear SVM (One-vs-Rest)
   - TF-IDF + Multinomial Naive Bayes (One-vs-Rest)
4. Evaluate each with multi-label precision/recall/F1 (see Phase 13 metrics)
   and pick the best-performing one — document why in `docs/`.
5. `backend/nlp/classify.py`: apply the chosen model to all activities,
   store results in `activity_categories` with `confidence` and
   `classification_method_id`.

**Test:** `tests/test_classification.py` on the held-out labeled set.

**Done when:** you have a documented comparison table and a working
classifier populating `activity_categories`.

---

## PHASE 6 — Department + Stakeholder Detection

**Goal:** Determine which department(s) and which stakeholder group(s) an
activity involves — independent of category.

**Tools:** Same as Phase 4/5 (spaCy, rapidfuzz, scikit-learn optional).

**Steps:**
1. `backend/nlp/department_detector.py`: match text against department
   names/aliases/keywords dictionary (fuzzy + exact). If 0 matches →
   `Unknown`; if 1 → `Single Department`; if 2+ → `Multiple Departments`;
   if clearly campus-wide (e.g. "Convocation", "NAAC visit") →
   `Institution-wide`.
2. `backend/nlp/stakeholder_detector.py`: rule-based classifier using
   keyword cues ("students", "faculty", "MoU", "alumni meet", etc.), falling
   back to `Unknown` when unclear.
3. Populate `activity_departments`, `activity_stakeholders`, and
   `institutional_activities.department_status_id`.

**Test:** `tests/test_department_detection.py`,
`tests/test_stakeholder_detection.py` against manually verified samples.

**Done when:** department/stakeholder fields are populated and spot-checked
correct on a sample.

---

## PHASE 7 — Human Review System

**Goal:** Let a human correct anything the automated pipeline got wrong or
was unsure about, with full audit history.

**Tools:** Flask (backend, built in Phase 10) or a simple standalone script
first if the API isn't ready yet.

**Steps:**
1. Populate `review_queue` automatically for any activity with
   `overall_confidence < 0.60` (medium/low threshold from Phase 1 config).
2. Build review actions: edit field, mark duplicate, merge, verify source,
   verify LinkedIn match, approve/reject.
3. Every action writes a row to `review_history` (old value, new value,
   action, reviewer, timestamp, reason).
4. On approval, update `institutional_activities.verification_status`.

**Test:** `tests/test_review_workflow.py` — simulate an edit + approve cycle,
confirm history is recorded and the activity record updates correctly.

**Done when:** you can take a low-confidence record through the queue to
"Verified" status with a full audit trail.

---

## PHASE 8 — LinkedIn Cross-Reference

**Goal:** Attempt to find a matching TCE LinkedIn post for each website
activity — enrichment only, never mandatory.

**Tools:** Free/legitimate options only:
- **Manual verification for a defensible academic project** (recommended,
  zero cost, zero risk): search the public TCE LinkedIn page and paste
  matched post URLs/text into the system yourself for a sample. Completely
  legitimate and free.
- If you want automation: only use LinkedIn's **official Marketing/Community
  Management API** with proper developer app approval — this requires
  LinkedIn approval and is not guaranteed free/instant, so for the academic
  timeline, manual cross-reference is the practical free choice.
- **Do not** scrape LinkedIn by bypassing login/CAPTCHA — this violates
  LinkedIn's terms and the project's own rules (section 3 of the spec).

**Steps:**
1. `backend/linkedin/search_term_builder.py`: generate search terms per
   activity (title, date, department, person names, keywords).
2. Manually (or via approved API) look up the TCE LinkedIn page for a
   matching post within a reasonable date window.
3. Store result in `linkedin_matches` with `match_status` = `Matched`,
   `Possible Match`, `Not Found`, or `Not Checked` (never claim "Not Found"
   means "doesn't exist" — see spec section 20).
4. Keep the website activity regardless of match result.

**Test:** `tests/test_linkedin_matching.py` — validate that matched/unmatched
activities are still all present in `institutional_activities`.

**Done when:** a defensible subset of activities has honestly recorded
LinkedIn match status.

---

## PHASE 9 — Analytics

**Goal:** Compute the year-wise, department-wise, category-wise, and
stakeholder-wise statistics the dashboard and NL query system will use.

**Tools:** `pandas`, plain SQL queries.

**Steps:**
1. `backend/analytics/yearly.py`, `department.py`, `category.py`,
   `stakeholder.py`, `linkedin_visibility.py`, `data_quality.py` — each
   computing aggregate counts/trends straight from the database (no
   hardcoded numbers).
2. Cache expensive aggregations if needed, but always recomputable from
   the DB — never a static/frozen "demo" number.

**Test:** `tests/test_analytics.py` — verify totals reconcile (e.g. sum of
per-department counts roughly relates to overall totals, accounting for
multi-department activities).

**Done when:** every analytics function returns numbers that trace directly
back to real rows in the database.

---

## PHASE 10 — Flask API (backend)

**Goal:** Expose the data and analytics over HTTP for the frontend.

**Tools:** `Flask`, `flask-cors` (free).

**Steps:**
1. `backend/app.py` — Flask app factory, register blueprints from `routes/`.
2. Implement endpoints exactly as scoped:
   `GET /api/activities`, `/api/activities/:id`, `/api/years`,
   `/api/departments`, `/api/categories`, `/api/stakeholders`,
   `/api/analytics/overview|yearly|departments|categories|stakeholders|linkedin`,
   `/api/search`, `/api/review`, `POST /api/review/:id`,
   `POST /api/collection/run`.
3. Add pagination (`?page=&page_size=`), input validation, parameterized
   SQL queries (never string-concatenated SQL), structured logging, and
   consistent JSON error responses.

**Test:** `tests/test_api.py` using Flask's test client — hit each endpoint,
check status codes and response shape.

**Done when:** `flask run` starts locally and every listed endpoint responds
correctly against your real (even if small) dataset.

---

## PHASE 11 — React Dashboard (frontend)

**Goal:** Build the visual application.

**Tools:** `React` (via Vite — faster and lighter than create-react-app,
still free), a free chart library (`recharts` or `chart.js`), plain CSS or
Tailwind (free).

**Steps:**
1. `npm create vite@latest frontend -- --template react`
2. Pages: Dashboard, Activities, Activity Details, Five-Year Analysis,
   Departments, Categories, Stakeholders, Sports, NCC, NSS,
   LinkedIn Analysis, Review Queue, Data Sources, Reports, Natural
   Language Query.
3. `frontend/src/services/api.js` — a thin wrapper around `fetch()` calling
   your Flask API (use an environment variable for the base URL so it works
   both locally and once deployed).
4. Global filters (year, semester, date range, department, category,
   stakeholder, source, confidence, verification status) as shared
   React state/context, applied consistently across pages.
5. KPI cards and charts driven entirely by `/api/analytics/*` responses —
   never hardcoded numbers.

**Test:** Manually verify each page renders real data from your local Flask
API; add a couple of React component smoke tests if time allows
(`vitest` + `@testing-library/react`, both free).

**Done when:** the dashboard runs locally (`npm run dev`) against your local
API and every chart/number reflects the actual database.

---

## PHASE 12 — Natural-Language Query System

**Goal:** Let a user type a question in plain English and get a real,
grounded answer — safely.

**Tools:** Keep this **rule-based/pattern-based first** (free, explainable,
defensible for an academic project) rather than jumping straight to an LLM:

**Steps (recommended free approach):**
1. `backend/nlp/query_parser.py`: use pattern matching + spaCy to extract
   intent (count/list/compare), entities (year, department, category,
   stakeholder) from the question.
2. Map the parsed intent to one of a **fixed, pre-approved set of safe,
   parameterized SQL query templates** — never build/execute freeform SQL
   from user text. This guarantees read-only, injection-safe behavior.
3. Return: answer text, the number/table, filters actually used, and (where
   applicable) the list of matching activities with their sources.
4. *(Optional, still free)* If you want smarter language understanding, you
   can call Anthropic's Claude API for **only the parsing step** (turning
   the question into a structured intent), still executing your own safe
   SQL templates — Anthropic gives free trial credits, but do not rely on
   this for the core deliverable since it wouldn't be free long-term unless
   you keep using free credits. The rule-based parser is the truly
   zero-cost, always-available option.

**Test:** `tests/test_nlq.py` with the exact example questions from the
spec (sports 2023-24, NCC counts, FDPs in 2024-25, department comparisons,
etc.) — confirm each maps to the correct template and returns the right
grounded numbers from your test data.

**Done when:** every sample question in the spec returns a correct,
sourced, non-fabricated answer.

---

## PHASE 13 — Evaluation + Testing

**Goal:** Rigorously measure both NLP performance and data quality —
kept as two clearly separate reports.

**Tools:** `scikit-learn.metrics` (precision, recall, F1, confusion matrix).

**Steps:**
1. Use the manually labeled ground-truth subset from Phase 5.
2. Compute: multi-label precision/recall/F1 (macro & micro), department
   detection accuracy, stakeholder detection accuracy, entity extraction
   precision/recall, duplicate detection precision/recall, LinkedIn
   matching accuracy (on the manually verified subset).
3. Separately, compute the **data quality dashboard** numbers: raw records,
   valid records, duplicates found, final unique activities, missing
   dates/departments, unknown categories/stakeholders, low-confidence
   records, review/verification counts, collection failures.
4. Write both reports to `data/evaluation/` as CSV/JSON, kept distinct from
   institutional activity statistics.

**Test:** `tests/test_evaluation_metrics.py` — sanity-check metric
calculations against a small hand-computed example.

**Done when:** you have defensible, reproducible NLP metrics and a
data-quality report, generated from real evaluation code (not eyeballed).

---

## PHASE 14 — Reports, Documentation, Presentation

**Goal:** Produce the final academic deliverables.

**Tools:** Python (`pandas.to_csv`, `openpyxl` for Excel — free), a PDF
library (`reportlab` or `fpdf2` — free) or export from the React dashboard.

**Steps:**
1. Generate the 31-section report (Executive Summary → Conclusion, as
   listed in the spec) — populate every section from real computed data,
   analytics outputs, and evaluation results, not placeholder text.
2. Export CSV/Excel/PDF versions from `backend/analytics` outputs.
3. Prepare a presentation deck summarizing findings, five-year trends,
   data quality, and NLP evaluation — again grounded in the real numbers.
4. Final `README.md` update covering setup, architecture, and how to
   reproduce every result.

**Done when:** the report, exports, and presentation are complete and every
number in them traces back to the database.

---

# FREE DEPLOYMENT GUIDE

Everything below uses **free tiers only** — no credit card charges, though
some platforms may ask for a card on file for identity verification (Render,
Railway) without charging unless you exceed free limits, which this
project's scale won't.

## Recommended free stack

| Component | Free service | Why |
|---|---|---|
| Frontend (React) | **Vercel** or **Netlify** (free tier) | Auto-deploys from GitHub, free HTTPS, generous free bandwidth |
| Backend (Flask API) | **Render.com** free web service *or* **PythonAnywhere** free tier | Free Python hosting, HTTPS included |
| Database | **SQLite file on Render's persistent disk (free tier)**, or **Neon.tech / Supabase free Postgres** if you want guaranteed persistence | See note below on SQLite + free hosting |
| Source code | **GitHub** (free, public or private repos) | Needed for auto-deploy triggers |

> **Important note on SQLite in production:** Most free hosting platforms
> (Render free web services, Railway free tier) restart your app periodically
> and may not guarantee a persistent filesystem, which can silently reset a
> SQLite `.db` file. Two free-safe options:
> 1. Use **Render's free persistent disk add-on** (available on the free
>    plan with size limits) and point `DATABASE_PATH` at it.
> 2. Migrate to a **free-tier hosted Postgres** (Neon.tech or Supabase both
>    have permanent free tiers) — your schema was written in portable SQL
>    specifically so this migration is straightforward later.
> For an academic project, option 1 (persistent disk on Render free tier) is
> simplest; option 2 is more robust if you want zero risk of data loss.

## Step-by-step deployment

### 1. Push your code to GitHub (free)
```bash
cd tce-activity-intelligence
git init
git add .
git commit -m "Initial commit"
# Create a new empty repo on github.com first, then:
git remote add origin https://github.com/<your-username>/tce-activity-intelligence.git
git branch -M main
git push -u origin main
```

### 2. Deploy the Flask backend on Render (free)
1. Go to [render.com](https://render.com) → sign up free with GitHub.
2. **New → Web Service** → connect your repo.
3. Settings:
   - **Root directory:** `backend`
   - **Build command:** `pip install -r ../requirements.txt`
   - **Start command:** `gunicorn app:app` (add `gunicorn` to `requirements.txt`)
   - **Instance type:** Free
4. Add a **free persistent disk** (Render dashboard → Disks) mounted at
   e.g. `/data`, and set an environment variable `DATABASE_PATH=/data/tce_activity_intelligence.db`
   so your `backend/config.py` reads it (`os.environ.get("DATABASE_PATH", default)`).
5. After first deploy, use Render's **Shell** tab to run
   `python backend/database/init_db.py` and `seed_reference_data.py` once,
   against the persistent disk.
6. Note your backend's public URL, e.g. `https://tce-backend.onrender.com`.

*(Free tier note: Render free web services "sleep" after inactivity and take
~30–50 seconds to wake on the next request — fine for an academic demo, just
mention it during your presentation.)*

### 3. Deploy the React frontend on Vercel (free)
1. Go to [vercel.com](https://vercel.com) → sign up free with GitHub.
2. **New Project** → import your repo → set **Root Directory** to `frontend`.
3. Framework preset: Vite (auto-detected).
4. Add an environment variable `VITE_API_BASE_URL=https://tce-backend.onrender.com`
   and use it in `frontend/src/services/api.js` instead of a hardcoded URL.
5. Deploy — Vercel gives you a free `https://your-project.vercel.app` URL
   with HTTPS automatically.

### 4. Enable CORS on the backend
In `backend/app.py`:
```python
from flask_cors import CORS
CORS(app, origins=["https://your-project.vercel.app"])
```

### 5. (Optional) Free custom subdomain
Both Vercel and Render let you attach a free subdomain of a domain you
already own, or you can simply use the free `*.vercel.app` / `*.onrender.com`
URLs for the academic submission — no cost either way.

### 6. Verify the deployed system
- Open the Vercel URL, confirm the dashboard loads and shows real numbers
  (not zeros/errors) by hitting the live Render API.
- Test 2–3 natural-language questions from Phase 12 against the live
  deployment.
- Take screenshots for your report/presentation while it's live.

## Cost summary

| Item | Cost |
|---|---|
| GitHub repo | Free |
| Render free web service + free persistent disk | Free |
| Vercel free frontend hosting | Free |
| SQLite / free-tier Postgres (Neon/Supabase) | Free |
| spaCy, scikit-learn, Flask, React, all libraries used | Free, open-source |
| LinkedIn cross-reference (manual method) | Free |
| **Total** | **₹0 / $0** |

---

## Final checklist before submission

- [ ] Every phase's tests pass and were actually run (not assumed).
- [ ] No fabricated activities, dates, departments, or LinkedIn posts exist
      anywhere in the database.
- [ ] Data quality dashboard numbers are real and traceable.
- [ ] NLP evaluation metrics are computed from a real ground-truth subset.
- [ ] Deployed frontend + backend are live and demonstrated with real data.
- [ ] Final report's 31 sections are all filled from actual project outputs.
