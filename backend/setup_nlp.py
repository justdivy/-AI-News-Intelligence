"""Download the spaCy model and NLTK data used by this project."""

import nltk
import spacy
from spacy.cli import download as download_spacy_model


SPACY_MODEL = "en_core_web_sm"
NLTK_RESOURCES = ("punkt", "punkt_tab", "stopwords")


def main() -> None:
    """Install NLP assets into the active Python environment."""
    try:
        spacy.load(SPACY_MODEL)
        print(f"spaCy model '{SPACY_MODEL}' is already available.")
    except OSError:
        print(f"Downloading spaCy model '{SPACY_MODEL}'...")
        download_spacy_model(SPACY_MODEL)

    for resource in NLTK_RESOURCES:
        print(f"Checking NLTK resource '{resource}'...")
        if not nltk.download(resource, raise_on_error=True):
            raise RuntimeError(f"Could not download NLTK resource '{resource}'.")

    print("NLP setup is complete.")


if __name__ == "__main__":
    main()
