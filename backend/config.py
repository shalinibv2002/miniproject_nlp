import hashlib
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATABASE_PATH = os.environ.get(
    "DATABASE_PATH",
    os.path.join(BASE_DIR, "data", "tce_activity_intelligence.db"),
)

RAW_DATA_DIR = os.path.join(BASE_DIR, "data", "raw")
EVALUATION_DIR = os.path.join(BASE_DIR, "data", "evaluation")
EXPORT_DIR = os.path.join(BASE_DIR, "data", "exports")

SPACY_MODEL = os.environ.get("SPACY_MODEL", "en_core_web_sm")

REQUEST_USER_AGENT = os.environ.get(
    "REQUEST_USER_AGENT",
    "TCEActivityIntelligence/1.0 (academic research project; respectful-crawler)",
)
REQUEST_DELAY_SECONDS = float(os.environ.get("REQUEST_DELAY_SECONDS", "2"))
REQUEST_RETRIES = int(os.environ.get("REQUEST_RETRIES", "3"))
REQUEST_TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT", "30"))

# Step 2: discovery is deliberately bounded by pages, never by an activity
# count.  The defaults keep a live academic crawl polite and controllable.
CRAWL_ALLOWED_DOMAINS = tuple(
    d.strip().lower() for d in os.environ.get("CRAWL_ALLOWED_DOMAINS", "tce.edu").split(",") if d.strip()
)
CRAWL_ALLOW_SUBDOMAINS = os.environ.get("CRAWL_ALLOW_SUBDOMAINS", "0") == "1"
# Step 2 expansion ceiling. This remains bounded and can be lowered without
# modifying crawler code.
TCE_DISCOVERY_MAX_SOURCES = int(os.environ.get("TCE_DISCOVERY_MAX_SOURCES", "500"))
CRAWL_MAX_PAGES = int(os.environ.get("CRAWL_MAX_PAGES", str(TCE_DISCOVERY_MAX_SOURCES)))
CRAWL_MAX_DEPTH = int(os.environ.get("CRAWL_MAX_DEPTH", "3"))
CRAWL_ENABLE_PDFS = os.environ.get("CRAWL_ENABLE_PDFS", "1") != "0"
CRAWL_ENABLE_PAGINATION = os.environ.get("CRAWL_ENABLE_PAGINATION", "1") != "0"

REVIEW_CONFIDENCE_THRESHOLD = float(os.environ.get("REVIEW_CONFIDENCE_THRESHOLD", "0.60"))

MAX_PAGE_SIZE = int(os.environ.get("MAX_PAGE_SIZE", "100"))
DEFAULT_PAGE_SIZE = int(os.environ.get("DEFAULT_PAGE_SIZE", "20"))

# Phase 8 — LinkedIn cross-reference (free, legitimate workflow only).
# 'manual' = build search terms + CSV lookup sheet, human records results.
LINKEDIN_AUTO_METHOD = os.environ.get("LINKEDIN_AUTO_METHOD", "manual")
LINKEDIN_PAGE_HANDLE = os.environ.get("LINKEDIN_PAGE_HANDLE", "https://www.linkedin.com/company/tcemadurai")

# Admin area — lightweight token-session sign in for the demo project.
# Only the SHA-256 digest of the password is stored; the plaintext password is
# never kept in the repository, logs, API responses, or documentation.
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "shalini")
ADMIN_PASSWORD_HASH = os.environ.get(
    "ADMIN_PASSWORD_HASH",
    "0a49fde8a5c691a2ee02a600c508a56db6007815ed2afba757daa7bcb17a8f45",
)
ADMIN_SESSION_TTL_SECONDS = int(os.environ.get("ADMIN_SESSION_TTL_SECONDS", "28800"))

# Standard user login — role 'user' for public analytics/drilldown pages.
# Default credentials: username "tce_user", password "tce2026".
USER_USERNAME = os.environ.get("USER_USERNAME", "tce_user")
USER_PASSWORD_HASH = os.environ.get(
    "USER_PASSWORD_HASH",
    hashlib.sha256("tce2026".encode("utf-8")).hexdigest(),
)
USER_SESSION_TTL_SECONDS = int(os.environ.get("USER_SESSION_TTL_SECONDS", "28800"))
