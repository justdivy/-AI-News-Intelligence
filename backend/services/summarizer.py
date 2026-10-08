"""Frequency-based extractive summarization."""

from collections import Counter
from typing import Any

from nltk import sent_tokenize

from services.preprocessing import preprocess_text


def summarize_text(text: str, max_sentences: int = 3) -> dict[str, Any]:
    """Select informative source sentences using article-specific word frequencies."""
    if not isinstance(text, str):
        raise TypeError("Article text must be a string.")
    if (
        not isinstance(max_sentences, int)
        or isinstance(max_sentences, bool)
        or max_sentences < 1
    ):
        raise ValueError("max_sentences must be a positive integer.")

    try:
        sentences = [sentence.strip() for sentence in sent_tokenize(text) if sentence.strip()]
    except LookupError as error:
        raise RuntimeError(
            "NLTK sentence data is missing. From the backend folder, run: python setup_nlp.py"
        ) from error

    if not sentences:
        return {
            "summary": "",
            "sentences": [],
            "source_sentence_count": 0,
            "summary_sentence_count": 0,
            "method": "extractive word-frequency ranking",
        }

    sentence_tokens = [
        preprocess_text(sentence)["content_tokens"] for sentence in sentences
    ]
    frequencies = Counter(token for tokens in sentence_tokens for token in tokens)

    scored_sentences = []
    for index, (sentence, tokens) in enumerate(zip(sentences, sentence_tokens)):
        # Average normalized frequency rewards key terms without favoring long sentences.
        score = (
            sum(frequencies[token] / len(frequencies) for token in tokens) / len(tokens)
            if tokens and frequencies
            else 0.0
        )
        scored_sentences.append({"index": index, "text": sentence, "score": score})

    chosen = sorted(
        sorted(scored_sentences, key=lambda item: (-item["score"], item["index"]))[
            :max_sentences
        ],
        key=lambda item: item["index"],
    )

    return {
        "summary": " ".join(item["text"] for item in chosen),
        "sentences": chosen,
        "source_sentence_count": len(sentences),
        "summary_sentence_count": len(chosen),
        "method": "extractive word-frequency ranking",
    }
