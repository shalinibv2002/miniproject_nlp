# Model Selection Decision (Phase 5)

## Question
Which multi-label classifier should populate `activity_categories`?

## Approach
Four models were trained and evaluated on the same train/test split of the
labeled training corpus (`backend/nlp/labeled_data.py`, ~115 samples across
24 categories, multi-label):

1. Rule-Based Keyword Baseline (`RuleBasedClassifier`)
2. TF-IDF + Logistic Regression (One-vs-Rest, `class_weight="balanced"`)
3. TF-IDF + Linear SVM (One-vs-Rest, `class_weight="balanced"`)
4. TF-IDF + Multinomial Naive Bayes (One-vs-Rest)

Features: TF-IDF unigrams + bigrams over spaCy-lemmatized text. Vectorizer
is fitted on the training split only to avoid leakage.

## Results (held-out test split, macro-F1 / micro-F1)

| Model | Precision (macro) | Recall (macro) | F1 (macro) | F1 (micro) |
|---|---|---|---|---|
| Rule-Based Keyword Baseline | 0.74 | 0.78 | **0.73** | 0.83 |
| TF-IDF + LogisticRegression (OvR) | 0.33 | 0.27 | 0.29 | 0.41 |
| TF-IDF + LinearSVC (OvR) | 0.29 | 0.23 | 0.25 | 0.37 |
| TF-IDF + MultinomialNB (OvR) | 0.00 | 0.00 | 0.00 | 0.00 |

Full comparison output: `data/evaluation/model_comparison.csv` and
`data/evaluation/model_comparison.json`.

## Why the rule-based baseline won
- The labeled corpus (a few samples per category) is small for a 24-class
  multi-label task, so the TF-IDF models overfit sparse decision boundaries
  and, in several cases, predicted no labels at sensibly low ratios.
- Keyword cues are highly discriminative for the strongly keyword-driven
  categories (workshop, hackathon, FDP, STTP, NCC, NSS, webinar, sports).
- NB/Multinomial failed (all-zero predictions) given the extreme
  positive-class sparsity per label.

## Decision
Use the **Rule-Based Keyword Baseline** as the production classifier for
`activity_categories`. It is deterministic, explainable, injection-free, and
scored highest macro-F1 (0.73) on the held-out set.

To re-run: `python -m backend.nlp.train_models` then
`python -m backend.nlp.classify`.

## Caveat
As more real labeled activities become available, re-run
`train_and_compare()` — at ~150+ real labeled records the TF-IDF models are
expected to overtake the rules. The pipeline is designed to make that switch
a single command.