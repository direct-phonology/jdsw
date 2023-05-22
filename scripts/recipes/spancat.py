from functools import partial
from typing import Any, Callable, Container, Dict, Iterable, Iterator, Optional, Union

import prodigy
import spacy
from nltk.util import ngrams
from prodigy.components.loaders import get_stream
from prodigy.types import RelationsTask
from prodigy.util import set_hashes, split_string
from spacy.language import Language
from spacy.pipeline.spancat import Suggester
from spacy.tokens import Doc, Span
from thinc.api import Ops, get_current_ops
from thinc.types import Ragged

from scripts.lib.components import doc_spans_jdsw
from scripts.lib.patterns import SPAN_LABELS


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

        # rehash since we added data
        eg = set_hashes(eg)
        yield eg


def validate_spans(eg: RelationsTask) -> bool:
    """Validate Jingdian Shiwen spans."""
    # TODO: validate that spans are within the suggested chunks
    spans = eg.get("spans", [])
    return True


@prodigy.recipe(
    "jdsw.spans.correct",
    dataset=("Dataset to save annotations to", "positional", None, str),
    source=(
        "Data to annotate (file path or '-' to read from standard input)",
        "positional",
        None,
        str,
    ),
    loader=("Loader (guessed from file extension if not set)", "option", "lo", str),
    labels=(
        "Comma-separated label(s) to annotate or text file with one label per line",
        "option",
        "l",
        split_string,
    ),
)
def jdsw_spans_correct(
    dataset: str,
    source: Union[str, Iterable[dict]],
    loader: Optional[str] = None,
    labels: Container[str] = SPAN_LABELS,
) -> Dict[str, Any]:
    """Annotate spans in JDSW annotations by correcting rule-based predictions."""
    # set up the character-based tokenizer
    nlp = spacy.blank("zh")

    # stream in the data, tokenize, and add the predicted spans and labels
    stream = get_stream(source, loader=loader, input_key="text")
    stream = make_tasks(nlp, stream, labels)

    # set up the recipe
    return {
        "dataset": dataset,
        "stream": stream,
        "view_id": "spans_manual",
        # "validate_answer": validate_spans,
        "config": {
            "labels": labels,
        },
    }
