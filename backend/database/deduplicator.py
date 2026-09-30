"""Fuzzy deduplication using rapidfuzz on normalized titles + date + text."""

from rapidfuzz import fuzz

from backend.database.normalizer import to_normalized_title

HIGH_MATCH_THRESHOLD = 95.0
PENDING_LOW = 70.0


def _title_ratio(a, b):
    """Weighted fuzzy ratio - good at catching word-order/additions."""
    return float(fuzz.WRatio(a, b))


def _date_neutral(record):
    """Normalize None/empty dates to '' for equality comparison."""
    return (record.get("activity_date") or "").strip()


def compare_pair(record_a, record_b):
    """Compare two records. Returns (score, is_high_confidence).

    Auto-merge: fuzzy title ratio >= 95 AND same date (or both dates empty).
    Anything at or above PENDING_LOW is a candidate for human review.
    """
    norm_a = to_normalized_title(record_a.get("title", ""))
    norm_b = to_normalized_title(record_b.get("title", ""))
    if not norm_a or not norm_b:
        return 0.0, False

    ratio = _title_ratio(norm_a, norm_b)
    same_date = _date_neutral(record_a) == _date_neutral(record_b) and bool(
        _date_neutral(record_a)
    )
    both_no_date = not _date_neutral(record_a) and not _date_neutral(record_b)

    if ratio >= HIGH_MATCH_THRESHOLD and (same_date or both_no_date):
        return ratio, True
    return ratio, False


def both_empty(record_a, record_b):
    return not _date_neutral(record_a) and not _date_neutral(record_b)


def find_duplicates(records):
    """Pairwise scan records -> two lists:
      - auto_merge: list of (record_a, record_b, score)
      - pending:    list of (record_a, record_b, score)
    """
    auto_merge = []
    pending = []
    seen = set()
    for i in range(len(records)):
        for j in range(i + 1, len(records)):
            if (j, i) in seen:
                continue
            a, b = records[i], records[j]
            score, high = compare_pair(a, b)
            if high:
                auto_merge.append((a, b, score))
                seen.add((i, j))
            elif score >= PENDING_LOW:
                pending.append((a, b, score))
                seen.add((i, j))
    return auto_merge, pending


def deduplicate(records):
    """Return records list with high-confidence duplicates merged
    (keeping the first occurrence; later occurrences dropped) plus a list
    of duplicate_candidates rows to persist."""
    auto_merge, pending = find_duplicates(records)
    merged_out = set()
    candidates = []
    merge_map = {}

    for a, b, score in auto_merge:
        key_a = id(a)
        key_b = id(b)
        target = merge_map.get(key_a, key_a)
        if target in merged_out or key_a == key_b:
            continue
        if key_b in merge_map and merge_map[key_b] in merged_out:
            continue
        merged_out.add(key_b)
        merge_map[key_b] = target

    for a, b, score in pending:
        candidates.append({
            "activity_id_a": None,
            "activity_id_b": None,
            "similarity_score": round(score / 100.0, 4),
            "match_reason": "fuzzy-title-similarity",
            "status": "Pending",
        })

    for key in merged_out:
        for a, b, score in auto_merge:
            if key == id(b):
                candidates.append({
                    "activity_id_a": None,
                    "activity_id_b": None,
                    "similarity_score": round(score / 100.0, 4),
                    "match_reason": "fuzzy-title+date",
                    "status": "Auto-Merged",
                })

    result = []
    kept_ids = set()
    for record in records:
        if id(record) not in merged_out and id(record) not in kept_ids:
            result.append(record)
            kept_ids.add(id(record))
    return result, candidates