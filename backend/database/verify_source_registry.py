"""Update source_registry with URLs verified against the live TCE website
(Phase 2 step 1). The originally-seeded rows were placeholders."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database.init_db import get_connection

VERIFIED_URLS = {
    "TCE Events": ("https://www.tce.edu/events", "events"),
    "TCE Academics": ("https://www.tce.edu/academics/programmes", "academics"),
    "TCE Departments": ("https://www.tce.edu/academics/departments", "departments"),
    "TCE Sports": ("https://www.tce.edu/campuslife/sports", "sports"),
    "TCE NCC": ("https://www.tce.edu/campuslife/ncc", "ncc"),
    "TCE NSS": ("https://www.tce.edu/campuslife/nss", "nss"),
    "TCE Clubs": ("https://clubs.tceapps.in/tce/student", "clubs"),
    "TCE Achievements": ("https://www.tce.edu/ranking-recognition", "achievements"),
    "TCE Outreach": ("https://www.tce.edu/campuslife/nss", "outreach"),
    "TCE Newsletter": (
        "https://www.tce.edu/sites/default/files/PDF/TCE-Newsletter-2026-Final-Corrected-Version.pdf",
        "newsletter",
    ),
}


def verify_source_registry(conn=None, db_path=None):
    from backend.database.init_db import get_connection as gc

    own = conn is None
    conn = conn or gc(db_path)
    updated = 0
    try:
        for name, (url, source_type) in VERIFIED_URLS.items():
            cur = conn.execute(
                "UPDATE source_registry SET url=?, source_type=?, notes='URL verified against live tce.edu' WHERE name=?",
                (url, source_type, name),
            )
            updated += cur.rowcount
        conn.commit()
        print(f"Updated {updated} source_registry rows with verified URLs.")
        for row in conn.execute("SELECT name, url, source_type FROM source_registry ORDER BY id"):
            print(f"  - {row['name']}: {row['url']} ({row['source_type']})")
        return updated
    finally:
        if own:
            conn.close()


if __name__ == "__main__":
    verify_source_registry()