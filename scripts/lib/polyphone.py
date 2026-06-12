"""
Extract polyphone-disambiguation training data from aligned JDSW annotations.

Each record pairs a character occurrence in its textual context with the
Middle Chinese reading Lu Deming assigned to it, derived from a fanqie or
duruo (音X) gloss and validated against the Guangyun where possible.
"""

import re
from dataclasses import dataclass
from typing import Any, Iterator, Optional

from scripts.lib.alignment import align_sequence, alternate_graphs, layer_at
from scripts.lib.phonology import (
    MultipleReadingsError,
    NoReadingError,
    Reconstruction,
)

FANQIE = re.compile(r"(.)(.)反")
DURUO = re.compile(r"音(.)")

# how certain we are that a reading attaches to a specific character
VALIDATED = "validated"  # exactly one char in the span has this Guangyun reading
AMBIGUOUS = "ambiguous"  # more than one char in the span has this reading
UNVALIDATED = "unvalidated"  # no char in the span has this reading per Guangyun


@dataclass
class Reading:
    kind: str  # "fanqie" or "duruo"
    source: str  # the annotation snippet the reading was derived from
    mc: Optional[str]  # composed Middle Chinese transcription, if derivable


def extract_readings(annotation: str, rc: Reconstruction) -> list[Reading]:
    """Extract all phonological readings given in a JDSW annotation."""
    readings = []
    taken: set[int] = set()

    for match in FANQIE.finditer(annotation):
        taken.update(range(match.start(), match.end()))
        try:
            mc = rc.fanqie_reading_for(match.group(1), match.group(2))
        except (NoReadingError, MultipleReadingsError):
            mc = None
        readings.append(Reading("fanqie", match.group(0), mc))

    for match in DURUO.finditer(annotation):
        # skip 音 readings whose target is already part of a fanqie (音XY反)
        if any(i in taken for i in range(match.start(), match.end())):
            continue
        mcs = rc.readings_for(match.group(1))
        readings.append(Reading("duruo", match.group(0), mcs[0] if len(mcs) == 1 else None))

    return readings


def locate_targets(span_text: str, mc: str, rc: Reconstruction) -> tuple[list[int], str]:
    """
    Offsets within an aligned span whose Guangyun readings include the given
    reading, with a validation verdict.
    """
    hits = [i for i, char in enumerate(span_text) if rc.is_valid_reading(char, mc)]
    if len(hits) == 1:
        return hits, VALIDATED
    if len(hits) > 1:
        return hits, AMBIGUOUS
    return [], UNVALIDATED


def polyphone_records(
    entries: list[dict],
    text: str,
    rc: Reconstruction,
    context: int = 24,
    layers: Optional[list] = None,
) -> Iterator[dict[str, Any]]:
    """
    Yield (context, target char offset, reading) records for a sequence of
    JDSW annotation entries against the juan text they comment on.

    Entries are dicts as found in annotations.jsonl: {"text": <annotation>,
    "meta": {"headword": ..., ...}}, in JDSW order. Records with validation
    "ambiguous" or "unvalidated" are emitted flagged, so downstream consumers
    can filter on data quality. 如字 ("read as usual") glosses are not emitted,
    since they assign no specific reading.
    """
    lemmas = [entry["meta"]["headword"] for entry in entries]
    alternates = [alternate_graphs(entry["text"]) for entry in entries]
    matches = align_sequence(lemmas, text, alternates=alternates)

    for entry, match in zip(entries, matches):
        if not match.found:
            continue
        span_text = text[match.start : match.end]

        for reading in extract_readings(entry["text"], rc):
            if reading.mc is None:
                continue

            offsets, validation = locate_targets(span_text, reading.mc, rc)
            # if validation fails, fall back to the last character of the span
            if not offsets:
                offsets = [len(span_text) - 1]

            for offset in offsets:
                position = match.start + offset
                window_start = max(position - context, 0)
                yield {
                    "text": text[window_start : position + context + 1],
                    "offset": position - window_start,
                    "char": text[position],
                    "reading": reading.mc,
                    "kind": reading.kind,
                    "source": reading.source,
                    "annotation": entry["text"],
                    "headword": match.lemma,
                    "span": [match.start, match.end],
                    "validation": validation,
                    "alignment": match.confidence,
                    "layer": layer_at(layers or [], position),
                    "meta": entry.get("meta", {}),
                }
