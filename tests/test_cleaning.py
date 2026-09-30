"""Phase 3 tests: cleaning + normalization."""

from backend.database.cleaner import clean_text, clean_record, normalize_date, strip_html
from backend.database.normalizer import to_normalized_title


def test_strip_html():
    out = strip_html("<p>Hello <b>World</b></p>")
    assert out.strip().replace("  ", " ") == "Hello World"


def test_strip_script_style():
    html = "<script>var x=1;</script>Hello <style>.a{}</style> World"
    assert "Hello" in strip_html(html)
    assert "var x" not in strip_html(html)


def test_normalize_whitespace_and_unicode():
    assert clean_text("Hi\xa0there\n\n   friend") == "Hi there friend"


def test_normalize_date_iso():
    assert normalize_date("2024-03-15") == "2024-03-15"


def test_normalize_date_english_short():
    assert normalize_date("15 Mar 2024") == "2024-03-15"


def test_normalize_date_english_long():
    assert normalize_date("15 March 2024") == "2024-03-15"


def test_normalize_date_dmy():
    assert normalize_date("15/03/2024") == "2024-03-15"


def test_normalize_date_invalid():
    assert normalize_date("not a date") is None
    assert normalize_date("") is None
    assert normalize_date(None) is None


def test_clean_record_date_field():
    record = {"title": "  Workshop  ", "activity_date": "15 Mar 2024"}
    cleaned = clean_record(record)
    assert cleaned["title"] == "Workshop"
    assert cleaned["activity_date"] == "2024-03-15"
    assert record["title"] == "  Workshop  "  # original unchanged


def test_normalized_title():
    assert to_normalized_title("Hello, World!") == "hello world"
    assert to_normalized_title("  NLP   & AI  ") == "nlp ai"


def test_clean_record_venue_organizer():
    record = {"title": "T", "venue": "  Seminar   Hall  ", "organizer": "Dept of CSE "}
    cleaned = clean_record(record)
    assert cleaned["venue"] == "Seminar Hall"
    assert cleaned["organizer"] == "Dept of CSE"