import re
from functools import partial
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    Iterator,
    Optional,
    Union,
    List,
    Container,
)
from collections import defaultdict

import prodigy
import spacy
import srsly
from nltk.util import ngrams
from prodigy.components.loaders import get_stream
from prodigy.components.preprocess import add_tokens
from prodigy.types import RelationsTask
from prodigy.util import set_hashes, split_string
from spacy.pipeline.spancat import Suggester
from spacy.tokens import Doc, Span
from spacy.matcher import PhraseMatcher
from spacy.language import Language
from thinc.api import Ops, get_current_ops
from thinc.types import Ragged


if not Span.has_extension("atomic"):
    Span.set_extension("atomic", default=False)

if not Span.has_extension("possible_entity"):
    Span.set_extension("possible_entity", default=True)

SPAN_LABELS = ["SEM", "GRAF", "PHON", "META", "PER", "WORK"]
"""Labels for types of content in Jingdian Shiwen annotations."""

REL_LABELS = ["SRC", "MOD"]
"""Labels for types of relations between spans in Jingdian Shiwen annotations."""

MODIFIER = "上下又並同一或亦後末"
MODIFIER2 = "注皆章及文篇卦"
MARKER = "作云也同音無"
WORK = "書本文言子注經卦詩"

SPAN_PATTERN_MAP = {
    "PHON": [
        re.compile(rf"^[{MODIFIER}]*?音?(.)(.)之\1|\2$"),
        re.compile(rf"^[{MODIFIER}]*?音?..反$"),
        re.compile(rf"^[{MODIFIER}]*?音?如字$"),
        re.compile(rf"^[{MODIFIER}]*?音[^{MARKER}]$"),
    ],
    "SEM": [
        re.compile(rf"^[{MODIFIER}]*?[^{MARKER}]+也$"),
    ],
    "GRAF": [
        re.compile(rf"^[{MODIFIER}]*?[作無][^{MARKER}{MODIFIER}]+$"),
    ],
    "META": [
        re.compile(rf"^[{MODIFIER}{MODIFIER2}]+[^{MARKER}]*同$"),
        re.compile(r"^出注$"),
        re.compile(r"^絶句$"),
        re.compile(r"^字非$"),
    ],
    "MARKER": [
        re.compile(rf"^[{MODIFIER}]*?[{MARKER}]$"),
    ],
}

ENT_PATTERN_MAP = {
    "WORK": [
        re.compile(rf"^.*?[{WORK}]$"),
    ],
    "PER": [
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
XYZY_PATTERN = re.compile(r"音?(.)(.)之\1|\2")
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
    for match in matcher(doc):
        indices.append(match[1])
        indices.append(match[2])
    return split_at_indices(doc.text, sorted(list(set(indices))))


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

    # pass 4: span-initial characters
    spans = split_spans(spans, SPLIT_BEFORE.split)
    spans = split_spans(spans, SPLIT_BEFORE_2.split)  # ent + 同

    # pass 5: catchall entity detection
    for span in spans:
        for label, patterns in ENT_PATTERN_MAP.items():
            if any(pattern.fullmatch(span.text) for pattern in patterns):
                if not span.label_:  # don't overwrite existing labels
                    span.label_ = label
                    span._.atomic = True
                    span._.possible_entity = True

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


def span_ngram_suggester(
    docs: Iterable[Doc],
    doc_spans: Callable[[Doc], Iterable[Span]],
    *,
    ops: Optional[Ops] = None,
) -> Ragged:
    """Suggester for all ngrams within preselected spans of a document."""
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
        for span in doc_spans(doc):
            tokens = range(span.start, span.end)
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
    return partial(span_ngram_suggester, doc_spans=doc_spans_jdsw)


def make_tasks(
    nlp: Language,
    stream: Iterable[RelationsTask],
    labels: Container[str],
) -> Iterator[RelationsTask]:
    """Predict spans for a stream of examples using a rule-based approach."""
    texts = ((eg["text"], eg) for eg in stream)

    for text, eg in texts:
        doc = nlp.make_doc(text)

        # tokens
        tokens = [
            {
                "start": i,
                "end": i + 1,
                "text": char,
                "id": i,
                "ws": False,
                "disabled": char == "云",
            }
            for i, char in enumerate(text)
        ]
        eg["tokens"] = tokens

        # spans
        spans = doc_spans_jdsw(doc)
        prodigy_spans = [
            {
                "start": span.start,
                "end": span.end,
                "token_start": span.start,
                "token_end": span.end - 1,
                "label": span.label_,
            }
            for span in spans
            if span.label_ in labels
        ]
        eg["spans"] = prodigy_spans

        # relations
        rels = span_rels_jdsw(list(spans))
        eg["relations"] = rels

        # rehash since we added data
        eg = set_hashes(eg)
        yield eg


def validate_spans(eg: RelationsTask) -> bool:
    """Validate Jingdian Shiwen spans."""
    # TODO: validate that spans are within the suggested chunks
    spans = eg.get("spans", [])
    return True


@prodigy.recipe(
    "jdsw.correct",
    dataset=("Dataset to save annotations to", "positional", None, str),
    source=(
        "Data to annotate (file path or '-' to read from standard input)",
        "positional",
        None,
        str,
    ),
    loader=("Loader (guessed from file extension if not set)", "option", "lo", str),
    label=(
        "Comma-separated relation label(s) to annotate or text file with one label per line",
        "option",
        "r",
        split_string,
    ),
    span_label=(
        "Comma-separated span label(s) to annotate or text file with one label per line",
        "option",
        "l",
        split_string,
    ),
)
def jdsw_correct(
    dataset: str,
    source: Union[str, Iterable[dict]],
    loader: Optional[str] = None,
    label: Container[str] = REL_LABELS,
    span_label: Container[str] = SPAN_LABELS,
) -> Dict[str, Any]:
    """Annotate spans and relations in JDSW annotations by correcting rule-based predictions."""
    # set up the character-based tokenizer
    nlp = spacy.blank("zh")

    # stream in the data, tokenize, and add the predicted spans and labels
    stream = get_stream(source, loader=loader, input_key="text")
    stream = make_tasks(nlp, stream, span_label)

    # set up the recipe
    return {
        "dataset": dataset,
        "stream": stream,
        "view_id": "relations",
        # "validate_answer": validate_spans,
        "config": {
            "labels": label,
            "relations_span_labels": span_label,
        },
    }
