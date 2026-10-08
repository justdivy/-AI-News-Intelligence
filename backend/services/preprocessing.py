"""Text cleaning, tokenization, and stopword filtering."""

import html
import re
import string
from typing import Any

from nltk import word_tokenize
from nltk.corpus import stopwords


_URL_PATTERN = re.compile(r"(?:https?://|www\.)\S+", flags=re.IGNORECASE)
_HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
_WHITESPACE_PATTERN = re.compile(r"\s+")
_PUNCTUATION_TABLE = str.maketrans({character: " " for character in string.punctuation})


def clean_text(text: str) -> str:
    """Decode HTML entities, remove markup and URLs, lowercase, and normalize spaces."""
    decoded_text = html.unescape(text)
    without_markup = _HTML_TAG_PATTERN.sub(" ", decoded_text)
    without_urls = _URL_PATTERN.sub(" ", without_markup)
    lowercased = without_urls.lower()
    return _WHITESPACE_PATTERN.sub(" ", lowercased).strip()


def preprocess_text(text: str) -> dict[str, Any]:
    """Return cleaned text, tokens, and stopword-filtered text for an article."""
    if not isinstance(text, str):
        raise TypeError("Article text must be a string.")

    cleaned_text = clean_text(text)
    if not cleaned_text:
        return {
            "cleaned_text": "",
            "punctuation_free_text": "",
            "tokens": [],
            "content_tokens": [],
            "processed_text": "",
            "token_count": 0,
            "content_token_count": 0,
        }

    try:
        punctuation_free_text = _WHITESPACE_PATTERN.sub(
            " ", cleaned_text.translate(_PUNCTUATION_TABLE)
        ).strip()
        tokens = word_tokenize(punctuation_free_text, language="english")
        stopword_set = set(stopwords.words("english"))
    except LookupError as error:
        raise RuntimeError(
            "NLTK data is missing. From the backend folder, run: python setup_nlp.py"
        ) from error

    # Keep alphabetic tokens only: punctuation and numeric-only fragments are excluded.
    normalized_tokens = [token for token in tokens if token.isalpha()]
    content_tokens = [token for token in normalized_tokens if token not in stopword_set]

    return {
        "cleaned_text": cleaned_text,
        "punctuation_free_text": punctuation_free_text,
        "tokens": normalized_tokens,
        "content_tokens": content_tokens,
        "processed_text": " ".join(content_tokens),
        "token_count": len(normalized_tokens),
        "content_token_count": len(content_tokens),
    }
