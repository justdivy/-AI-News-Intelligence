"""Part-of-speech tagging with spaCy."""

from collections import Counter
from typing import Any

from spacy import explain

from services.spacy_model import load_spacy_model


def tag_parts_of_speech(text: str) -> dict[str, Any]:
    """Return spaCy's Universal POS and fine-grained tag for each text token."""
    if not isinstance(text, str):
        raise TypeError("Article text must be a string.")

    doc = load_spacy_model()(text)
    tagged_tokens = []
    pos_counts: Counter[str] = Counter()

    for token in doc:
        if token.is_space:
            continue
        tag_description = explain(token.tag_) if token.tag_ else None
        tagged_tokens.append(
            {
                "token": token.text,
                "pos": token.pos_,
                "tag": token.tag_,
                "description": tag_description or token.pos_ or "Unclassified",
            }
        )
        if token.pos_:
            pos_counts[token.pos_] += 1

    return {
        "tags": tagged_tokens,
        "token_count": len(tagged_tokens),
        "pos_counts": dict(sorted(pos_counts.items())),
    }
