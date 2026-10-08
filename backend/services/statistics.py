"""Article word-frequency calculations."""

from collections import Counter
from typing import Any

from services.preprocessing import preprocess_text


def analyze_word_frequency(text: str, top_n: int = 10) -> dict[str, Any]:
    """Count preprocessed content words and return the most frequent terms."""
    if not isinstance(text, str):
        raise TypeError("Article text must be a string.")
    if not isinstance(top_n, int) or isinstance(top_n, bool) or top_n < 1:
        raise ValueError("top_n must be a positive integer.")

    content_tokens = preprocess_text(text)["content_tokens"]
    counts = Counter(content_tokens)
    ranked_words = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:top_n]

    return {
        "frequencies": [
            {"word": word, "count": count} for word, count in ranked_words
        ],
        "content_word_count": len(content_tokens),
        "unique_content_word_count": len(counts),
    }
