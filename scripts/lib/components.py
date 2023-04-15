import re
import json
from typing import List, Iterable, Tuple, Callable
from collections import namedtuple, defaultdict

from pathlib import Path
import spacy
import srsly
from spacy.language import Language
from spacy.matcher import PhraseMatcher

# from spacy.tokens import Doc, Span

MODIFIER = "上下又並同一或亦"
PHON_PATTERN = re.compile(rf"([{MODIFIER}]?音?(?:(?:..反)|音.|如字))")
XYZY_PATTERN = re.compile(r"(.)(.)之\1|\2")
SPLIT_AFTER = re.compile(r"(.+?[也同]+)")
SPLIT_AROUND = re.compile(rf"([{MODIFIER}]?云)")
SPLIT_BEFORE = re.compile(rf"([{MODIFIER}]?作.+)")

# GRAPHIC = re.compile(r"(.+?)([上下又並同一或亦]?作.)")


# individual span formats
## fanqie (modifier + 音? + AB + 反)
## yin (modifier + 音 + X)
## ruzi (modifier + 如字)
## xyzy (XY + 之 + X/Y)
## semantic (anything ending in 也)
## meta (anything ending in 同); "出注" or "絶句"??
## graphic (entity + 作 + X)
## entity (anything preceding a 作 or 云)
### book (ending with 書 or 本)
### person (1-3 characters)

SEMANTIC = re.compile(r"^[^云作]+?也$")
GRAPHIC = re.compile(rf"^[{MODIFIER}]?作[^云也]*$")
META = re.compile(r"^[^作云也]*?同$")
WORK_OF_ART = re.compile(r"^.*?[書本文言子注經卦]$")
PERSON = re.compile(r"^[^云作也書本文言注經]{1,2}$")
COMMENTARY = re.compile(r"^.+注.+$")

Span = namedtuple("Span", ["text", "label"])

# entity_patterns = [json.loads(pattern) for pattern in Path("assets/ner_patterns.jsonl").read_text().splitlines()]
# entities = set(pattern['pattern'] for pattern in entity_patterns)


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


def split_spans(
    spans: Iterable[Span],
    pattern: re.Pattern,
    split_fn: Callable[[str], List[str]] = None,
) -> List[Span]:
    """
    Use a pattern to split each unlabeled span, returning a flattened list of spans.
    If split_fn is provided, use it to split the span instead of the pattern.
    """
    output: List[Span] = []
    _split_fn = split_fn or pattern.split

    for span in spans:
        if span.label:
            output.append(span)
            continue

        for item in _split_fn(span.text):
            if item:
                output.append(Span(item, None))

    return output


def label_spans(
    spans: Iterable[Span],
    pattern: re.Pattern,
    label: str,
) -> List[Span]:
    """For each unlabeled span, label it if it matches the pattern."""

    output: List[Span] = []

    for span in spans:
        if span.label:
            output.append(span)
            continue

        if pattern.match(span.text):
            output.append(Span(span.text, label))
        else:
            output.append(span)

    return output


def split_and_label_spans(
    spans: Iterable[Span],
    pattern: re.Pattern,
    label: str = None,
    split_fn: Callable[[str], List[str]] = None,
) -> List[Span]:
    """
    For each unlabeled span, split it using the pattern and label the result if it matches the pattern.
    If split_fn is provided, use it to split the span instead of the pattern.
    """
    output: List[Span] = []
    _split_fn = split_fn or pattern.split

    for span in spans:
        if span.label:
            output.append(span)
            continue

        for item in _split_fn(span.text):
            if item:
                if pattern.match(item):
                    output.append(Span(item, label))
                else:
                    output.append(Span(item, None))

    return output


def label_via_matcher(spans: Iterable[Span], matcher: PhraseMatcher, nlp: spacy.Language) -> List[Span]:
    """For each unlabeled span, label it if it matches a phrase in the matcher."""
    output: List[Span] = []

    for span in spans:
        doc = nlp.make_doc(span.text)
        matches = matcher(doc)



    return output


def doc_to_spans(doc: str) -> List[Span]:
    # first pass: split and label phonetic patterns
    spans = [Span(doc, None)]
    spans = split_and_label_spans(spans, PHON_PATTERN, label="PHONETIC")
    spans = split_and_label_spans(
        spans,
        XYZY_PATTERN,
        label="PHONETIC",
        split_fn=lambda s: split_backref_noncapture(s, XYZY_PATTERN),
    )

    # second pass: split semantic, graphic, meta patterns
    spans = split_spans(spans, SPLIT_AFTER)
    spans = split_spans(spans, SPLIT_AROUND)
    spans = split_spans(spans, SPLIT_BEFORE)

    # third pass: split known entities
    # patterns = defaultdict(list)
    # for pattern in srsly.read_jsonl('assets/ner_patterns.jsonl'):
    #     patterns[pattern['label']].append(pattern['pattern'])

    # nlp = spacy.blank("zh")
    # matcher = PhraseMatcher(nlp.vocab, None)
    # for label, _patterns in patterns.items():
    #     matcher.add(label, [nlp.make_doc(pattern) for pattern in _patterns])

    # final pass: labeling
    spans = label_spans(spans, SEMANTIC, "SEMANTIC")
    spans = label_spans(spans, META, "META")
    spans = label_spans(spans, GRAPHIC, "GRAPHIC")

    # commentary entities
    spans = label_spans(spans, COMMENTARY, "WORK_OF_ART")

    # catch-all for entities
    for i, span in enumerate(spans):
        if "云" in span.text or span.label == "GRAPHIC":
            if not spans[i - 1].label:
                if WORK_OF_ART.match(spans[i - 1].text):
                    spans[i - 1] = Span(spans[i - 1].text, "WORK_OF_ART")
                elif PERSON.match(spans[i - 1].text):
                    spans[i - 1] = Span(spans[i - 1].text, "PERSON")

    return spans


def str_to_doc(text: str) -> spacy.tokens.Doc:
    """Convert a string to a spaCy Doc."""
    nlp = spacy.blank("zh")

    doc = nlp(text)

    return doc
