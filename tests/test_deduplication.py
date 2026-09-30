"""Phase 3 tests: deduplication."""

from backend.database.deduplicator import compare_pair, find_duplicates, deduplicate


def test_exact_duplicates_detected():
    a = {"title": "National Workshop on AI", "activity_date": "2024-02-10"}
    b = {"title": "National Workshop on AI", "activity_date": "2024-02-10"}
    score, high = compare_pair(a, b)
    assert high is True
    assert score == 100.0


def test_near_duplicate_with_same_date_pending():
    a = {"title": "National Workshop on Artificial Intelligence", "activity_date": "2024-02-10"}
    b = {"title": "National Workshop on AI", "activity_date": "2024-02-10"}
    score, high = compare_pair(a, b)
    assert high is False
    assert score >= 70  # should still surface in the review queue


def test_different_dates_not_auto_merged():
    a = {"title": "National Workshop on AI", "activity_date": "2024-02-10"}
    b = {"title": "National Workshop on AI", "activity_date": "2024-03-15"}
    score, high = compare_pair(a, b)
    assert high is False


def test_different_titles_not_duplicates():
    a = {"title": "Workshop on AI", "activity_date": "2024-02-10"}
    b = {"title": "Independence Day Celebration", "activity_date": "2024-02-10"}
    score, high = compare_pair(a, b)
    assert high is False
    assert score < 75


def test_find_duplicates_partition():
    records = [
        {"title": "International Conference on IoT", "activity_date": "2024-01-05"},
        {"title": "International Conference on IoT", "activity_date": "2024-01-05"},
        {"title": "Sports Day 2024", "activity_date": "2024-01-20"},
        {"title": "Sports Day 2024 Celebration", "activity_date": "2024-01-20"},
    ]
    auto_merge, pending = find_duplicates(records)
    assert len(auto_merge) >= 1
    assert len(pending) >= 1


def test_deduplicate_merges_and_returns_candidates():
    records = [
        {"title": "Workshop on Machine Learning", "activity_date": "2024-02-10"},
        {"title": "Workshop on Machine Learning", "activity_date": "2024-02-10"},
        {"title": "Unique Seminar", "activity_date": "2024-03-01"},
    ]
    deduped, candidates = deduplicate(records)
    assert len(deduped) == 2
    auto = [c for c in candidates if c["status"] == "Auto-Merged"]
    assert len(auto) == 1


def test_deduplicate_keeps_uniques():
    records = [
        {"title": "A", "activity_date": "2024-01-01"},
        {"title": "B", "activity_date": "2024-02-02"},
        {"title": "C", "activity_date": "2024-03-03"},
    ]
    deduped, candidates = deduplicate(records)
    assert len(deduped) == 3
    assert candidates == []