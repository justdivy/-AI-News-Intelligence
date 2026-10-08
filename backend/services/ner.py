"""Named entity recognition with spaCy's English small pipeline."""

from typing import Any

from services.spacy_model import load_spacy_model


ENTITY_GROUPS = {
    "people": {"PERSON"},
    "organizations": {"ORG"},
    "locations": {"GPE", "LOC", "FAC"},
    "dates": {"DATE"},
    "money": {"MONEY"},
}

ENTITY_DESCRIPTIONS = {
    "PERSON": "Person",
    "ORG": "Organization",
    "GPE": "Location",
    "LOC": "Location",
    "FAC": "Facility",
    "DATE": "Date or time",
    "MONEY": "Monetary value",
}


def extract_entities(text: str) -> dict[str, Any]:
    """Find supported entities and group their unique surface forms."""
    if not isinstance(text, str):
        raise TypeError("Article text must be a string.")

    doc = load_spacy_model()(text)
    occurrences: list[dict[str, Any]] = []
    grouped_values: dict[str, list[str]] = {group: [] for group in ENTITY_GROUPS}
    seen_values: dict[str, set[str]] = {group: set() for group in ENTITY_GROUPS}

    for span in doc.ents:
        label = span.label_
        group = next(
            (group_name for group_name, labels in ENTITY_GROUPS.items() if label in labels),
            None,
        )
        if group is None:
            continue

        value = span.text.strip()
        occurrences.append(
            {
                "text": value,
                "label": label,
                "type": ENTITY_DESCRIPTIONS.get(label, label),
                "start": span.start_char,
                "end": span.end_char,
            }
        )

        normalized_value = value.casefold()
        if normalized_value not in seen_values[group]:
            grouped_values[group].append(value)
            seen_values[group].add(normalized_value)

    return {
        "entities": occurrences,
        "groups": grouped_values,
        "entity_count": len(occurrences),
        "unique_entity_count": sum(len(values) for values in grouped_values.values()),
        "category_counts": {group: len(values) for group, values in grouped_values.items()},
    }
