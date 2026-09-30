"""Phase 4 tests: regex + spaCy NER + dictionary department extraction."""

from backend.nlp import extractors


SAMPLES = [
    (
        "The International Workshop on AI was held at the Seminar Hall on 15 Feb 2024. "
        "Resource person: Dr. R. Kumar, organized by the Department of Computer Science.",
        "dr r kumar",
    ),
]


def test_extract_venue_regex():
    text = "The workshop was held at the A.C. Tech Seminar Hall on 15 Feb 2024."
    assert extractors.extract_venue(text) is not None


def test_extract_venue_absent():
    assert extractors.extract_venue("No venue mentioned anywhere.") is None


def test_extract_resource_person_regex():
    text = "Resource person: Dr. Rajesh Kumar. The talk covered AI."
    person = extractors.extract_resource_person(text)
    assert person is not None and "Rajesh" in person


def test_extract_resource_person_chief_guest():
    text = "Chief guest: Prof. Meena Subramanian graced the occasion."
    person = extractors.extract_resource_person(text)
    assert person is not None and "Meena" in person


def test_extract_organizer_regex():
    text = "The event organized by the Department of Mechanical Engineering was well attended."
    org = extractors.extract_organizer(text)
    assert org is not None and "Mechanical" in org


def test_extract_department_mentions_exact():
    text = "organized by the Department of Computer Science and Engineering, Madurai"
    matches = extractors.extract_department_mentions(text)
    assert any(m["code"] == "CSE" for m in matches)


def test_extract_department_mentions_unknown():
    assert extractors.extract_department_mentions("A completely unrelated generic text about painting.") == []


def test_extract_spacy_person_and_org():
    nlp = extractors.get_nlp()
    if nlp is None:
        return
    text = "Dr. A. P. J. Abdul Kalam delivered a lecture on Bharat 2020."
    entities = extractors.extract_spacy_entities(text, nlp)
    types = {e["entity_type"] for e in entities}
    assert "PERSON" in types or "ORG" in types


def test_extract_keywords():
    kws = extractors.extract_keywords("artificial intelligence machine learning workshop")
    assert "intelligence" in kws
    assert all(len(k) >= 4 for k in kws)


def test_extract_all_structure():
    text = "International Workshop on NLP held at Seminar Hall, resource person Dr. Suresh, org by Dept of ECE."
    results = extractors.extract_all(text)
    assert "dates" in results
    assert "venue" in results
    assert "departments" in results
    assert "keywords" in results