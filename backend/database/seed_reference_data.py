"""Seed ONLY fixed reference/lookup data. No activity records."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database.init_db import init_db, get_connection

ACADEMIC_YEARS = [
    {"name": "2020-2021", "start_year": 2020, "end_year": 2021},
    {"name": "2021-2022", "start_year": 2021, "end_year": 2022},
    {"name": "2022-2023", "start_year": 2022, "end_year": 2023},
    {"name": "2023-2024", "start_year": 2023, "end_year": 2024},
    {"name": "2024-2025", "start_year": 2024, "end_year": 2025},
]

DEPARTMENTS = [
    {"code": "CIVIL", "name": "Civil Engineering", "short_name": "Civil",
     "aliases": "civil, civil engineering, ce dept, civil dept"},
    {"code": "MECH", "name": "Mechanical Engineering", "short_name": "Mech",
     "aliases": "mech, mechanical, mechanical engineering, me dept"},
    {"code": "EEE", "name": "Electrical and Electronics Engineering", "short_name": "EEE",
     "aliases": "eee, electrical, electrical and electronics engineering"},
    {"code": "ECE", "name": "Electronics and Communication Engineering", "short_name": "ECE",
     "aliases": "ece, electronics and communication engineering, electronics & communication"},
    {"code": "CSE", "name": "Computer Science and Engineering", "short_name": "CSE",
     "aliases": "cse, computer science, computer science and engineering, comp sc"},
    {"code": "IT", "name": "Information Technology", "short_name": "IT",
     "aliases": "it, information technology, info tech"},
    {"code": "AUTO", "name": "Automobile Engineering", "short_name": "Auto",
     "aliases": "automobile, automobile engineering, auto dept, auto"},
    {"code": "MCT", "name": "Mechatronics Engineering", "short_name": "MCT",
     "aliases": "mechatronics, mechatronics engineering, mct"},
    {"code": "CHEM", "name": "Chemical Engineering", "short_name": "Chem Engg",
     "aliases": "chemical, chemical engineering, chem engg"},
    {"code": "MATH", "name": "Applied Mathematics and Computational Sciences", "short_name": "AMCS",
     # No bare "mathematics" / "maths" alias: Mathematics is a separate
     # department (code MATHS below).  A bare alias here is what used to route a
     # "Department of Mathematics" post into Applied Mathematics.
     "aliases": "applied mathematics, applied maths, amcs, computational sciences"},
    {"code": "MATHS", "name": "Mathematics", "short_name": "Maths",
     "aliases": "maths, mathematics, dept of mathematics, department of mathematics"},
    {"code": "PHY", "name": "Physics", "short_name": "Physics",
     "aliases": "physics, dept of physics"},
    {"code": "FASH", "name": "Fashion Technology", "short_name": "Fashion Tech",
     "aliases": "fashion technology, fashion tech, dept of fashion technology"},
    {"code": "CHE", "name": "Chemistry", "short_name": "Chemistry",
     "aliases": "chemistry, dept of chemistry"},
    {"code": "ENG", "name": "English and Humanities", "short_name": "English",
     "aliases": "english, humanities, dept of english, language lab"},
    {"code": "MBA", "name": "Management Studies", "short_name": "MBA",
     "aliases": "mba, management studies, department of management studies"},
]

CATEGORIES = [
    {"code": "WORKSHOP", "name": "Workshop",
     "description": "Hands-on skill-building workshops"},
    {"code": "SEMINAR", "name": "Seminar",
     "description": "Academic and technical seminars"},
    {"code": "CONFERENCE", "name": "Conference",
     "description": "National/international conferences"},
    {"code": "SYMPOSIUM", "name": "Symposium",
     "description": "Technical symposiums"},
    {"code": "GUEST_LECTURE", "name": "Guest Lecture",
     "description": "Invited lectures by experts"},
    {"code": "FDP", "name": "Faculty Development Programme",
     "description": "Faculty development and upskilling programs"},
    {"code": "STTP", "name": "Short Term Training Programme",
     "description": "Short term training courses"},
    {"code": "HACKATHON", "name": "Hackathon",
     "description": "Coding and innovation hackathons"},
    {"code": "TECH_FEST", "name": "Technical Festival",
     "description": "Technical and annual college festivals"},
    {"code": "CULTURAL", "name": "Cultural Event",
     "description": "Cultural programs and celebrations"},
    {"code": "SPORTS", "name": "Sports and Games",
     "description": "Sports events, tournaments, athletics"},
    {"code": "NCC", "name": "NCC Activity",
     "description": "National Cadet Corps activities"},
    {"code": "NSS", "name": "NSS Activity",
     "description": "National Service Scheme activities"},
    {"code": "CLUB", "name": "Clubs and Chapters",
     "description": "Student clubs, professional chapters, society meets"},
    {"code": "OUTREACH", "name": "Outreach and Extension",
     "description": "Community service, extension, rural outreach"},
    {"code": "INDUSTRY", "name": "Industry Collaboration",
     "description": "MoUs, industry visits, industry collaborations"},
    {"code": "ACHIEVEMENT", "name": "Achievement and Award",
     "description": "Awards, recognitions, honours"},
    {"code": "PLACEMENT", "name": "Placement Activity",
     "description": "Placement drives, career guidance, training for placement"},
    {"code": "INTERNSHIP", "name": "Internship",
     "description": "Student/faculty internships"},
    {"code": "RESEARCH", "name": "Research and Consultancy",
     "description": "Research projects, patents, publications, consultancy"},
    {"code": "ALUMNI", "name": "Alumni Event",
     "description": "Alumni meets and alumni engagement"},
    {"code": "ORIENTATION", "name": "Orientation and Convocation",
     "description": "Orientation, induction, convocation, graduation"},
    {"code": "CAMPUS", "name": "Campus Life",
     "description": "Admissions, campus facilities, general campus events"},
    {"code": "WEBINAR", "name": "Webinar",
     "description": "Online talks and webinars"},
]

STAKEHOLDERS = [
    {"code": "STUDENTS", "name": "Students",
     "description": "Undergraduate, postgraduate students"},
    {"code": "FACULTY", "name": "Faculty",
     "description": "Teaching staff"},
    {"code": "STAFF", "name": "Non-Teaching Staff",
     "description": "Administrative and support staff"},
    {"code": "ALUMNI", "name": "Alumni",
     "description": "Former students of TCE"},
    {"code": "INDUSTRY", "name": "Industry",
     "description": "Industries, companies, corporate partners"},
    {"code": "PARENTS", "name": "Parents",
     "description": "Parents and guardians"},
    {"code": "GOVERNMENT", "name": "Government and Agencies",
     "description": "Government bodies, funding agencies, AICTE, UGC, DST"},
    {"code": "COMMUNITY", "name": "Community and Society",
     "description": "Local community, schools, general public"},
]

CLASSIFICATION_METHODS = [
    {"name": "Rule-Based Keyword Baseline", "version": "1.0",
     "description": "Keyword/rule-based category assignment"},
    {"name": "TF-IDF + LogisticRegression (OvR)", "version": "1.0",
     "description": "TF-IDF features with One-vs-Rest Logistic Regression"},
    {"name": "TF-IDF + LinearSVC (OvR)", "version": "1.0",
     "description": "TF-IDF features with One-vs-Rest Linear SVM"},
    {"name": "TF-IDF + MultinomialNB (OvR)", "version": "1.0",
     "description": "TF-IDF features with One-vs-Rest Multinomial Naive Bayes"},
    {"name": "SpaCy NER", "version": "1.0",
     "description": "spaCy en_core_web_sm NER extraction"},
    {"name": "Regex Pattern Extraction", "version": "1.0",
     "description": "Regex-based date/venue/resource-person extraction"},
    {"name": "Dictionary Fuzzy Match", "version": "1.0",
     "description": "Dictionary + rapidfuzz fuzzy matching"},
    {"name": "Manual / Human Review", "version": "1.0",
     "description": "Human reviewer corrected/approved"},
]

DEPARTMENT_STATUSES = [
    {"code": "single", "label": "Single Department"},
    {"code": "multiple", "label": "Multiple Departments"},
    {"code": "institution_wide", "label": "Institution-wide"},
    {"code": "unknown", "label": "Unknown"},
]

VERIFICATION_STATUSES = [
    {"code": "pending", "label": "Pending"},
    {"code": "verified", "label": "Verified"},
    {"code": "needs_review", "label": "Needs Review"},
    {"code": "rejected", "label": "Rejected"},
]

# Starter source registry. URLs are PLACEHOLDERS until verified against
# https://www.tce.edu in Phase 2.
SOURCE_REGISTRY = [
    {"name": "TCE Events", "url": "https://www.tce.edu/events",
     "source_type": "events", "notes": "Placeholder - verify real URL in Phase 2."},
    {"name": "TCE Academics", "url": "https://www.tce.edu/academics",
     "source_type": "academics", "notes": "Placeholder - verify real URL in Phase 2."},
    {"name": "TCE Departments", "url": "https://www.tce.edu/departments",
     "source_type": "departments", "notes": "Placeholder - verify real URL in Phase 2."},
    {"name": "TCE Sports", "url": "https://www.tce.edu/sports",
     "source_type": "sports", "notes": "Placeholder - verify real URL in Phase 2."},
    {"name": "TCE NCC", "url": "https://www.tce.edu/ncc",
     "source_type": "ncc", "notes": "Placeholder - verify real URL in Phase 2."},
    {"name": "TCE NSS", "url": "https://www.tce.edu/nss",
     "source_type": "nss", "notes": "Placeholder - verify real URL in Phase 2."},
    {"name": "TCE Clubs", "url": "https://www.tce.edu/clubs",
     "source_type": "clubs", "notes": "Placeholder - verify real URL in Phase 2."},
    {"name": "TCE Achievements", "url": "https://www.tce.edu/achievements",
     "source_type": "achievements", "notes": "Placeholder - verify real URL in Phase 2."},
    {"name": "TCE Outreach", "url": "https://www.tce.edu/outreach",
     "source_type": "outreach", "notes": "Placeholder - verify real URL in Phase 2."},
    {"name": "TCE Newsletter", "url": "https://www.tce.edu/newsletter",
     "source_type": "newsletter", "notes": "Placeholder - verify real URL in Phase 2."},
]


def seed(conn=None, db_path=None):
    own_conn = conn is None
    conn = conn or get_connection(db_path)
    try:
        # If already seeded, skip re-insertion.
        existing = conn.execute("SELECT COUNT(*) AS n FROM academic_years").fetchone()["n"]
        if existing > 0:
            print("Reference data already present - skipping re-seed.")
            return

        for row in ACADEMIC_YEARS:
            conn.execute(
                "INSERT INTO academic_years (name, start_year, end_year) VALUES (?, ?, ?)",
                (row["name"], row["start_year"], row["end_year"]),
            )

        for row in DEPARTMENTS:
            conn.execute(
                "INSERT INTO departments (code, name, short_name, aliases) VALUES (?, ?, ?, ?)",
                (row["code"], row["name"], row["short_name"], row["aliases"]),
            )

        for row in CATEGORIES:
            conn.execute(
                "INSERT INTO categories (code, name, description) VALUES (?, ?, ?)",
                (row["code"], row["name"], row["description"]),
            )

        for row in STAKEHOLDERS:
            conn.execute(
                "INSERT INTO stakeholders (code, name, description) VALUES (?, ?, ?)",
                (row["code"], row["name"], row["description"]),
            )

        for row in CLASSIFICATION_METHODS:
            conn.execute(
                "INSERT INTO classification_methods (name, description, version) VALUES (?, ?, ?)",
                (row["name"], row["description"], row["version"]),
            )

        for row in DEPARTMENT_STATUSES:
            conn.execute(
                "INSERT INTO department_statuses (code, label) VALUES (?, ?)",
                (row["code"], row["label"]),
            )

        for row in VERIFICATION_STATUSES:
            conn.execute(
                "INSERT INTO verification_statuses (code, label) VALUES (?, ?)",
                (row["code"], row["label"]),
            )

        for row in SOURCE_REGISTRY:
            conn.execute(
                "INSERT INTO source_registry (name, url, source_type, notes) VALUES (?, ?, ?, ?)",
                (row["name"], row["url"], row["source_type"], row["notes"]),
            )

        conn.commit()
        print("Reference data seeded successfully.")
    finally:
        if own_conn:
            conn.close()


if __name__ == "__main__":
    init_db()
    seed()
    conn = get_connection()
    print(conn.execute("SELECT COUNT(*) AS n FROM departments").fetchone()["n"], "departments")
    print(conn.execute("SELECT COUNT(*) AS n FROM categories").fetchone()["n"], "categories")
    print(conn.execute("SELECT COUNT(*) AS n FROM stakeholders").fetchone()["n"], "stakeholders")
    print(conn.execute("SELECT COUNT(*) AS n FROM academic_years").fetchone()["n"], "academic years")
    print(conn.execute("SELECT COUNT(*) AS n FROM institutional_activities").fetchone()["n"], "activities (must be 0)")
    conn.close()