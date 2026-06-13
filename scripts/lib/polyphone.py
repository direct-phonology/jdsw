"""
Extract polyphone-disambiguation training data from aligned JDSW annotations.

Each record pairs a character occurrence in its textual context with the
Middle Chinese reading Lu Deming assigned to it. Readings come from four
sources, recorded in each record's "kind":

- "fanqie": a 反 spelling (X Y 反), composed against the Guangyun;
- "duruo": a 音 X homophone gloss;
- "ruzi": a 如字 "read as usual" gloss, resolved to the character's default
  reading via scripts/lib/ruzi.py;
- "scope": a reading propagated from one of the above to later occurrences of
  the same character, where Lu writes 下同 ("same below") or 注同 ("same in
  the 注", restricted to the commentary layer — hence layer-aware).
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
from scripts.lib.ruzi import DefaultReadings

FANQIE = re.compile(r"(.)(.)反")
DURUO = re.compile(r"音(.)")
RUZI = re.compile(r"如字")

# scope markers: a reading also applies to later occurrences of the character
SCOPE_DOWN = re.compile(r"下同|下皆同|後同|下放此|放此")  # any later occurrence
SCOPE_NOTE = re.compile(r"注同")  # later occurrences in the commentary (注) layer

# largest number of later occurrences a single scope marker will propagate to,
# a guard against a reading on a common character flooding the output
MAX_SCOPE = 64

# how certain we are that a reading attaches to a specific character
VALIDATED = "validated"  # exactly one char in the span has this Guangyun reading
AMBIGUOUS = "ambiguous"  # more than one char in the span has this reading
UNVALIDATED = "unvalidated"  # no char in the span has this reading per Guangyun


@dataclass
class Reading:
    kind: str  # "fanqie" or "duruo"
    source: str  # the annotation snippet the reading was derived from
    mc: Optional[str]  # composed Middle Chinese transcription, if derivable


@dataclass
class _Base:
    """A base reading placed at an absolute text position, kept for scope expansion."""

    position: int
    char: str
    reading: str
    annotation: str
    meta: dict


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


def _validate_char(char: str, mc: str, rc: Reconstruction) -> str:
    """Validation verdict for a reading assigned to a single known character."""
    return VALIDATED if rc.is_valid_reading(char, mc) else UNVALIDATED


def _record(
    position: int,
    reading: str,
    kind: str,
    source: str,
    validation: str,
    *,
    headword: str,
    span: list[int],
    alignment: str,
    annotation: str,
    meta: dict,
    text: str,
    context: int,
    layers: Optional[list],
    extra: Optional[dict] = None,
) -> dict[str, Any]:
    """Build one training record for a character occurrence at a text position."""
    window_start = max(position - context, 0)
    record = {
        "text": text[window_start : position + context + 1],
        "offset": position - window_start,
        "char": text[position],
        "reading": reading,
        "kind": kind,
        "source": source,
        "annotation": annotation,
        "headword": headword,
        "span": span,
        "validation": validation,
        "alignment": alignment,
        "layer": layer_at(layers or [], position),
        "meta": meta,
    }
    if extra:
        record.update(extra)
    return record


def _scope_targets(
    char: str,
    origin: int,
    text: str,
    boundary: int,
    layers: Optional[list],
    commentary_only: bool,
) -> list[int]:
    """
    Positions of later occurrences of char a scope marker propagates to: after
    origin, before boundary (the next explicit gloss of char), capped at
    MAX_SCOPE, and — for 注同 — restricted to commentary-layer positions.
    """
    targets = []
    pos = text.find(char, origin + 1)
    while pos != -1 and pos < boundary and len(targets) < MAX_SCOPE:
        if not commentary_only or layer_at(layers or [], pos) == "commentary":
            targets.append(pos)
        pos = text.find(char, pos + 1)
    return targets


def polyphone_records(
    entries: list[dict],
    text: str,
    rc: Reconstruction,
    context: int = 24,
    layers: Optional[list] = None,
    default_readings: Optional[DefaultReadings] = None,
) -> Iterator[dict[str, Any]]:
    """
    Yield (context, target char offset, reading) records for a sequence of
    JDSW annotation entries against the juan text they comment on.

    Entries are dicts as found in annotations.jsonl: {"text": <annotation>,
    "meta": {"headword": ..., ...}}, in JDSW order. Records with validation
    "ambiguous" or "unvalidated" are emitted flagged, so downstream consumers
    can filter on data quality. 如字 glosses are resolved when default_readings
    is given (else skipped). Explicit readings carrying 下同/注同 are then
    propagated to later occurrences of the same character as kind "scope".
    """
    lemmas = [entry["meta"]["headword"] for entry in entries]
    alternates = [alternate_graphs(entry["text"]) for entry in entries]
    matches = align_sequence(lemmas, text, alternates=alternates)

    records: list[dict[str, Any]] = []
    bases: list[_Base] = []
    # positions where each character receives an explicit reading; bounds how
    # far a scope marker propagates, since a later gloss overrides it
    gloss_positions: dict[str, list[int]] = {}

    def emit_base(position: int, char: str, mc: str, kind: str, source: str,
                  validation: str, entry: dict, match: Any,
                  extra: Optional[dict] = None) -> None:
        records.append(
            _record(position, mc, kind, source, validation,
                    headword=match.lemma, span=[match.start, match.end],
                    alignment=match.confidence, annotation=entry["text"],
                    meta=entry.get("meta", {}), text=text, context=context,
                    layers=layers, extra=extra)
        )
        bases.append(_Base(position, char, mc, entry["text"], entry.get("meta", {})))
        gloss_positions.setdefault(char, []).append(position)

    # pass 1: explicit readings (fanqie, duruo, 如字)
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
                emit_base(position, text[position], reading.mc, reading.kind,
                          reading.source, validation, entry, match)

        if default_readings and RUZI.search(entry["text"]):
            for offset, char in enumerate(span_text):
                mc, _ = default_readings.resolve(char)
                if mc is None:
                    continue
                position = match.start + offset
                emit_base(position, char, mc, "ruzi", "如字",
                          _validate_char(char, mc, rc), entry, match,
                          extra={"ruzi_confidence": default_readings.confidence(char),
                                 "ruzi_signals_agree": default_readings.signals_agree(char)})

    # pass 2: scope expansion of explicit readings carrying 下同/注同
    scope_records: list[dict[str, Any]] = []
    for base in bases:
        commentary_only = bool(SCOPE_NOTE.search(base.annotation))
        down = SCOPE_DOWN.search(base.annotation)
        if not commentary_only and not down:
            continue
        later = [p for p in gloss_positions.get(base.char, []) if p > base.position]
        boundary = min(later) if later else len(text)
        source = "注同" if commentary_only else down.group(0)
        for position in _scope_targets(
            base.char, base.position, text, boundary, layers, commentary_only
        ):
            scope_records.append(
                _record(position, base.reading, "scope", source,
                        _validate_char(base.char, base.reading, rc),
                        headword=base.char, span=[position, position + 1],
                        alignment="scope", annotation=base.annotation, meta=base.meta,
                        text=text, context=context, layers=layers,
                        extra={"scope_from": base.position})
            )

    yield from records
    yield from scope_records
