"""Phase 5 preprocessing: tokenize, remove stopwords, lemmatize, TF-IDF features."""

import re

from sklearn.feature_extraction.text import TfidfVectorizer

from backend.nlp.extractors import get_nlp

_nlp_singleton = None


def _get_nlp():
    global _nlp_singleton
    if _nlp_singleton is None:
        _nlp_singleton = get_nlp()
    return _nlp_singleton


def clean_for_vectorization(text):
    if not text:
        return ""
    t = re.sub(r"[^a-z0-9\s]", " ", text.lower())
    return re.sub(r"\s+", " ", t).strip()


def lemmatize(text):
    """Tokenize, remove stopwords, lemmatize using spaCy."""
    nlp = _get_nlp()
    if nlp is None:
        return clean_for_vectorization(text)
    doc = nlp(text.lower())
    lemmas = []
    for token in doc:
        if token.is_stop or token.is_punct or token.is_space or not token.is_alpha:
            continue
        lemma = token.lemma_.strip()
        if lemma and len(lemma) > 1:
            lemmas.append(lemma)
    return " ".join(lemmas)


def build_tfidf(lemmatized_texts, ngram_range=(1, 2), min_df=1):
    """Fit_and_transform optionally: returns (vectorizer, matrix)."""
    vectorizer = TfidfVectorizer(ngram_range=ngram_range, min_df=min_df)
    matrix = vectorizer.fit_transform(lemmatized_texts)
    return vectorizer, matrix