import re
from collections import defaultdict
from typing import Any, Callable, Dict, Iterable, List

import spacy
import srsly
from spacy.matcher import PhraseMatcher
from spacy.tokens import Doc, Span
from spacy.util import filter_spans

from scripts.lib.patterns import (
    PHON_PATTERN,
    SPAN_LABELS,
    SPAN_PATTERN_MAP,
    SPLIT_AFTER,
    SPLIT_AROUND,
    SPLIT_AROUND_2,
    SPLIT_BEFORE,
    SPLIT_BEFORE_2,
    SPLIT_BEFORE_3,
    XYZY_PATTERN,
)

if not Span.has_extension("atomic"):
    Span.set_extension("atomic", default=False)

if not Span.has_extension("possible_entity"):
    Span.set_extension("possible_entity", default=True)

# pre-defined entity patterns
patterns = defaultdict(list)
for pattern in srsly.read_jsonl("assets/ner_patterns.jsonl"):
    patterns[pattern["label"]].append(pattern["pattern"])

# set up a PhraseMatcher for pre-defined entities
nlp = spacy.blank("zh")
MATCHER = PhraseMatcher(nlp.vocab, None)
for label, _patterns in patterns.items():
    MATCHER.add(label, [nlp.make_doc(pattern) for pattern in _patterns])


def check_span(span: Span) -> Span:
    """Check whether a span contains entities and/or is atomic, and set the flags accordingly."""
    # spans of length 1 can no longer be split
    if len(span) == 1:
        span._.atomic = True

    # check if the span matches a known span pattern
    # if so, label it and mark it as atomic
    # also mark it as not containing any entities
    for label, patterns in SPAN_PATTERN_MAP.items():
        if any(pattern.fullmatch(span.text) for pattern in patterns):
            span.label_ = label
            span._.atomic = True
            span._.possible_entity = False
            return span

    # check if the span matches a known entity pattern, preferring longest match
    # if so, label it and mark it as atomic
    if span._.possible_entity:
        doc = span.as_doc()
        match_spans = []
        for label, start, end in MATCHER(doc):
            match_span = doc.char_span(start, end)
            match_span.label_ = nlp.vocab.strings[label]
            match_spans.append(match_span)
        matches = filter_spans(match_spans)
        if len(matches) == 1 and (matches[0].text == span.text):
            span.label_ = matches[0].label_
            span._.atomic = True
            return span

    return span


def split_spans(
    spans: Iterable[Span],
    split_fn: Callable[[str], List[str]],
) -> List[Span]:
    """
    Use a provided function to split each non-atomic span, yielding a flat list of spans.
    """
    output_spans = []
    _split_fn = split_fn

    def _split_span(span: Span) -> List[Span]:
        output_spans = []
        subspans = list(filter(bool, _split_fn(span.text)))

        # must be a non-destructive split
        assert "".join(subspans) == span.text

        subspan_start = 0
        for subspan in subspans:
            output_spans.append(
                span.doc.char_span(
                    span.start + subspan_start,
                    span.start + subspan_start + len(subspan),
                )
            )
            subspan_start += len(subspan)

        return output_spans

    for span in spans:
        if span._.atomic:
            output_spans.append(span)
        else:
            for subspan in _split_span(span):
                output_spans.append(check_span(subspan))

    return output_spans


def split_at_indices(text: str, indices: List[int]) -> List[str]:
    """Split a string at the given indices."""
    return [
        part
        for part in (text[i:j] for i, j in zip([0] + indices, indices + [None]))  # type: ignore
        if part
    ]


def split_backref_noncapture(text: str, pattern: re.Pattern) -> List[str]:
    """Split a string using a regex with backreferences, but don't capture the backreferences."""
    indices = []
    for match in pattern.finditer(text):
        indices.append(match.start())
        indices.append(match.end())
    return split_at_indices(text, sorted(list(set(indices))))


def split_phrase_matcher(doc: Doc, matcher: PhraseMatcher) -> List[str]:
    """Split a string using a provided PhraseMatcher instance."""
    indices = []
    spans = [doc[start:end] for _, start, end in matcher(doc)]
    for span in filter_spans(spans):
        indices.append(span.start)
        indices.append(span.end)
    return split_at_indices(doc.text, sorted(list(set(indices))))


def split_headwords(text: str, headword: str) -> List[str]:
    """Split a string using any characters from the headword."""
    indices = [i for i, char in enumerate(text) if char in headword]
    ranges = []
    for j, i in enumerate(indices):
        if j == 0:
            ranges.append([i, i + 1])
        elif indices[j - 1] == i - 1:
            ranges[-1][1] += 1
        else:
            ranges.append([i, i + 1])
    range_indices = [i for r in ranges for i in r]
    return split_at_indices(text, sorted(list(set(range_indices))))


def doc_spans_jdsw(doc: Doc) -> Iterable[Span]:
    """Split a Jingdian Shiwen annotation into (non-overlapping) labeled spans."""
    # start with the entire doc as a single span
    spans = [doc.char_span(0, len(doc.text))]

    # pass 1: phonetic patterns
    spans = split_spans(spans, PHON_PATTERN.split)
    spans = split_spans(spans, lambda s: split_backref_noncapture(s, XYZY_PATTERN))

    # pass 2: known entities
    spans = split_spans(spans, lambda s: split_phrase_matcher(nlp.make_doc(s), MATCHER))

    # pass 2: span-final characters
    spans = split_spans(spans, SPLIT_AFTER.split)

    # pass 3: span-separator characters
    spans = split_spans(spans, SPLIT_AROUND.split)
    spans = split_spans(spans, SPLIT_AROUND_2.split) # 非也

    # pass 4: span-initial characters
    spans = split_spans(spans, SPLIT_BEFORE.split)
    spans = split_spans(spans, SPLIT_BEFORE_2.split)  # ent + 同
    spans = split_spans(spans, SPLIT_BEFORE_3.split)  # 謂之

    # pass 5: restatements of headword
    # if headword := doc.user_data.get("headword"):
    #     spans = split_spans(spans, lambda s: split_headwords(s, headword))
    #     for span in spans:
    #         if span.text in headword:
    #             span.label_ = "HEAD"
    #             span._.atomic = True
    #             span._.possible_entity = False

    return spans


def span_rels_jdsw(spans: List[Span]) -> Iterable[Dict[str, Any]]:
    """Extract relations from Jingdian Shiwen spans."""
    rels: List[Dict[str, Any]] = []
    subtrees: List[List[Span]] = [[]]

    # first pass: add relations between meta spans and what they modify
    for i, span in enumerate(spans):
        if i > 0 and span.label_ == "META" and spans[i - 1].label_ in SPAN_LABELS:
            rels.append(
                {
                    "head": span.end - 1,
                    "child": spans[i - 1].end - 1,
                    "label": "MOD",
                }
            )

    # second pass: add relations between spans and their textual sources (entities)
    while len(spans):
        span = spans.pop(0)
        if span.label_ not in ["PER", "WORK"]:
            subtrees[-1].append(span)
        else:
            subtrees.append([span])
    for subtree in subtrees:
        if len(subtree) < 2:
            continue
        head = subtree[0]
        if head.label_ not in ["PER", "WORK"]:
            continue
        for span in subtree[1:]:
            if span.label_ in ["SEM", "GRAF", "PHON"]:
                rels.append(
                    {
                        "head": head.end - 1,
                        "child": span.end - 1,
                        "label": "SRC",
                    }
                )

    return rels
