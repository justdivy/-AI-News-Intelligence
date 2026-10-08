"""Sentence-level TF-IDF keyword extraction for a single article."""

from typing import Any

import numpy as np
from nltk import sent_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer

from services.preprocessing import preprocess_text


def extract_keywords(text: str, top_n: int = 10) -> dict[str, Any]:
    """Rank article terms by their TF-IDF weight across the article's sentences."""
    if not isinstance(text, str):
        raise TypeError("Article text must be a string.")
    if not isinstance(top_n, int) or isinstance(top_n, bool) or top_n < 1:
        raise ValueError("top_n must be a positive integer.")

    try:
        sentences = sent_tokenize(text, language="english")
    except LookupError as error:
        raise RuntimeError(
            "NLTK sentence data is missing. From the backend folder, run: python setup_nlp.py"
        ) from error

    processed_sentences = [
        preprocess_text(sentence)["processed_text"] for sentence in sentences
    ]
    processed_sentences = [sentence for sentence in processed_sentences if sentence]

    if not processed_sentences:
        return {"keywords": [], "sentence_count": 0, "method": "sentence-level TF-IDF"}

    vectorizer = TfidfVectorizer(
        tokenizer=str.split,
        preprocessor=None,
        token_pattern=None,
        lowercase=False,
        ngram_range=(1, 2),
        use_idf=True,
        smooth_idf=True,
        norm="l2",
    )

    try:
        sentence_term_matrix = vectorizer.fit_transform(processed_sentences)
    except ValueError as error:
        if "empty vocabulary" in str(error).lower():
            return {
                "keywords": [],
                "sentence_count": len(processed_sentences),
                "method": "sentence-level TF-IDF",
            }
        raise

    terms = vectorizer.get_feature_names_out()
    scores = np.asarray(sentence_term_matrix.sum(axis=0)).ravel()
    ranked_indices = sorted(range(len(terms)), key=lambda index: (-scores[index], terms[index]))
    selected = ranked_indices[:top_n]
    maximum_score = float(scores[selected[0]]) if selected else 0.0

    return {
        "keywords": [
            {
                "keyword": str(terms[index]),
                "score": float(scores[index]),
                "relative_score": float(scores[index] / maximum_score) if maximum_score else 0.0,
            }
            for index in selected
        ],
        "sentence_count": len(processed_sentences),
        "method": "sentence-level TF-IDF",
    }
