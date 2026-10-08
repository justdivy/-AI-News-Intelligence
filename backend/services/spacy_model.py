"""Shared loader for the spaCy model used by NLP services."""

from functools import lru_cache

import spacy
from spacy.language import Language


MODEL_NAME = "en_core_web_sm"


@lru_cache(maxsize=1)
def load_spacy_model() -> Language:
    """Load and cache the project's English spaCy pipeline."""
    try:
        return spacy.load(MODEL_NAME)
    except OSError as error:
        raise RuntimeError(
            f"spaCy model '{MODEL_NAME}' is missing. From the backend folder, run: "
            "python setup_nlp.py"
        ) from error
