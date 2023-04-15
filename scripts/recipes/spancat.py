import re
from functools import partial
from typing import Any, Callable, Dict, Iterable, Iterator, Optional, Union, List, Tuple
from collections import defaultdict

import prodigy
import spacy
import srsly
from nltk.util import ngrams
from prodigy.components.loaders import get_stream
from prodigy.components.preprocess import add_tokens
from prodigy.types import SpansExample
from prodigy.util import set_hashes, split_string
from spacy.pipeline.spancat import Suggester
from spacy.tokens import Doc, Span
from spacy.matcher import PhraseMatcher
from thinc.api import Ops, get_current_ops
from thinc.types import Ragged

# import debugpy

# debugpy.listen(5678)
# debugpy.wait_for_client()

if not Span.has_extension("atomic"):
    Span.set_extension("atomic", default=False)

if not Span.has_extension("possible_entity"):
    Span.set_extension("possible_entity", default=True)

SPAN_LABELS = ["SEMANTIC", "GRAPHIC", "PHONETIC", "META", "PERSON", "WORK_OF_ART"]
"""Labels for types of content in Jingdian Shiwen annotations."""

MODIFIER = "上下又並同一或亦後"
MODIFIER2 = "注皆章及文篇"
MARKER = "作云也同音無"
WORK = "書本文言子注經卦詩"

SPAN_PATTERN_MAP = {
    "PHONETIC": [
        re.compile(rf"^[{MODIFIER}]*?如字$"),
        re.compile(rf"^[{MODIFIER}]*?音?..反$"),
        re.compile(rf"^[{MODIFIER}]*?音[^{MARKER}]$"),
        re.compile(rf"^[{MODIFIER}]*?(.)(.)之\1|\2$"),
    ],
    "SEMANTIC": [
        re.compile(rf"^[{MODIFIER}]*?[^{MARKER}]+也$"),
    ],
    "GRAPHIC": [
        re.compile(rf"^[{MODIFIER}]*?[作無][^{MARKER}]+$"),
    ],
    "META": [
        re.compile(rf"^[{MODIFIER}{MODIFIER2}]+[^{MARKER}]*同$"),
    ],
    "MARKER": [
        re.compile(rf"^[{MODIFIER}]*?[{MARKER}]$"),
    ],
}

ENT_PATTERN_MAP = {
    "WORK_OF_ART": [
        re.compile(rf"^.*?[{WORK}]$"),
    ],
    "PERSON": [
        re.compile(rf"^[^{WORK}{MARKER}]{{1,3}}$"),
    ],
}

SPAN_PATTERNS = [
    pattern for patterns in SPAN_PATTERN_MAP.values() for pattern in patterns
]

ENT_PATTERNS = [
    pattern for patterns in ENT_PATTERN_MAP.values() for pattern in patterns
]

PHON_PATTERN = re.compile(rf"([{MODIFIER}]*?音?(?:(?:..反)|音.|如字))")
XYZY_PATTERN = re.compile(r"(.)(.)之\1|\2")
SPLIT_AFTER = re.compile(r"(.+?[也同]+)")
SPLIT_AROUND = re.compile(rf"([{MODIFIER}]*?[云])")
SPLIT_BEFORE = re.compile(rf"([{MODIFIER}]*?[作無][^{MARKER}]+)")
SPLIT_BEFORE_2 = re.compile(rf"([^{MARKER}{MODIFIER}{MODIFIER2}]+)(同)")

# pre-defined entity patterns
patterns = defaultdict(list)
for pattern in srsly.read_jsonl("assets/jdsw_ner_patterns.jsonl"):
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

    # check if the span matches a known entity pattern
    # if so, label it and mark it as atomic
    matches = MATCHER(span.as_doc())
    if len(matches) == 1 and (matches[0][2] - matches[0][1] == len(span)):
        span.label_ = nlp.vocab.strings[matches[0][0]]
        span._.atomic = True
        span._.possible_entity = True
        return span

    # catchall entity detection via regex
    for label, patterns in ENT_PATTERN_MAP.items():
        if any(pattern.fullmatch(span.text) for pattern in patterns):
            span.label_ = label
            span._.atomic = True
            span._.possible_entity = True
            return span

    return span


def split_spans(
    spans: Iterable[Span],
    # pattern: re.Pattern,
    split_fn: Callable[[str], List[str]],
) -> List[Span]:
    """
    Use a pattern to split each non-atomic span, yielding a flat list of spans.
    If split_fn is provided, use it to split the span instead of the pattern.
    """
    output_spans = []
    _split_fn = split_fn

    def _split_span(span: Span) -> List[Span]:
        output_spans = []
        chunks = list(filter(bool, _split_fn(span.text)))

        # must be a non-destructive split
        assert "".join(chunks) == span.text

        chunk_start = 0
        for chunk in chunks:
            output_spans.append(
                span.doc.char_span(
                    span.start + chunk_start, span.start + chunk_start + len(chunk)
                )
            )
            chunk_start += len(chunk)

        return output_spans

    for span in spans:
        if span._.atomic:
            output_spans.append(span)
        else:
            for chunk in _split_span(span):
                output_spans.append(check_span(chunk))

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
    for match in matcher(doc):
        indices.append(match[1])
        indices.append(match[2])
    return split_at_indices(doc.text, sorted(list(set(indices))))


def doc_chunks_jdsw(doc: Doc) -> Iterable[Span]:
    """Split a Jingdian Shiwen annotation into non-overlapping 'chunks'."""
    # start with the entire doc as a single span
    spans = [doc.char_span(0, len(doc.text))]

    # debugpy.breakpoint()

    # pass 1: full chunks
    spans = split_spans(spans, PHON_PATTERN.split)
    spans = split_spans(spans, lambda s: split_backref_noncapture(s, XYZY_PATTERN))

    # pass 2: known entities
    spans = split_spans(spans, lambda s: split_phrase_matcher(nlp.make_doc(s), MATCHER))

    # pass 2: chunk-final characters
    spans = split_spans(spans, SPLIT_AFTER.split)

    # pass 3: chunk-separator characters
    spans = split_spans(spans, SPLIT_AROUND.split)

    # pass 4: chunk-initial characters
    spans = split_spans(spans, SPLIT_BEFORE.split)
    spans = split_spans(spans, SPLIT_BEFORE_2.split)  # ent + 同

    # TODO: build parse tree

    return spans


def chunk_ngram_suggester(
    docs: Iterable[Doc],
    doc_chunks: Callable[[Doc], Iterable[Span]],
    *,
    ops: Optional[Ops] = None,
) -> Ragged:
    """Suggester for all ngrams within preselected chunks of a document."""
    # if we didn't specify gpu or cpu, use whatever is currently active
    if ops is None:
        ops = get_current_ops()

    # track spans as a flat list of [start, end] pairs
    # track number of spans per doc as an array of lengths
    # for every candidate span, add all its child ngrams to the list
    # TODO: only do child ngrams for spans that are not atomic
    spans = []
    lengths = []
    for doc in docs:
        length = 0
        for chunk in doc_chunks(doc):
            tokens = range(chunk.start, chunk.end)
            for i in range(1, len(tokens)):
                for ng in ngrams(i, tokens):
                    spans.append(ng)
                    length += 1
        lengths.append(length)
    lengths_array = ops.asarray1i(lengths)

    # reformat as a 2d ragged array
    if len(spans) > 0:
        output = Ragged(ops.xp.vstack(spans), lengths_array)
    else:
        output = Ragged(ops.xp.zeros((0, 0), dtype="i"), lengths_array)

    assert output.dataXd.ndim == 2
    return output


def build_jdsw_suggester() -> Suggester:
    """Suggest spans within Jingdian Shiwen annotations."""
    # TODO: support specifying a maximum ngram size
    return partial(chunk_ngram_suggester, doc_chunks=doc_chunks_jdsw)


def make_tasks(stream: Iterable[SpansExample]) -> Iterator[SpansExample]:
    """Predict spans for a stream of examples using a rule-based approach."""
    return (eg for eg in stream)


def validate_spans(eg: SpansExample) -> bool:
    """Validate Jingdian Shiwen spans."""
    # TODO: validate that spans are within the suggested chunks
    spans = eg.get("spans", [])
    return True


def spans_correct_ruler_jdsw(
    dataset: str,
    source: Union[str, Iterable[dict]],
    loader: Optional[str] = None,
) -> Dict[str, Any]:
    """Annotate spans in JDSW annotations by correcting rule-based predictions."""
    # set up the character-based tokenizer
    nlp = spacy.blank("zh")

    # stream in the data, tokenize, and add the predicted spans
    stream = get_stream(source, loader)
    stream = add_tokens(nlp, stream)
    stream = make_tasks(stream)

    # set up the recipe
    return {
        "dataset": dataset,
        "stream": stream,
        "view_id": "spans",
        # "validate_answer": validate_spans,
        "config": {
            "labels": SPAN_LABELS,
        },
    }
