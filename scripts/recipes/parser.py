from typing import Any, Dict, Iterable, List, Optional, Union, Iterator
from pathlib import Path

import spacy
import prodigy
from suparkanbun import DOWNLOAD_DIR
from supar import Parser
from suparkanbun import AutoModelTagger
from prodigy.components.loaders import get_stream
from prodigy.components.preprocess import add_tokens
from prodigy.util import split_string, set_hashes
from prodigy.types import DepExample

UD = ["acl", "advcl", "advmod", "amod", "appos", "aux", "case", "cc", "ccomp", "clf", "compound", "conj", "cop", "csubj", "dep", "det", "discourse", "dislocated", "expl", "fixed", "flat", "goeswith", "iobj", "list", "mark", "nmod", "nsubj", "nummod", "obj", "obl", "orphan", "parataxis", "punct", "reparandum", "root", "vocative", "xcomp"]

SENT_TAGS = ["B", "E", "E2", "E3", "M", "S"]

def segment_sentences(text: str, senter: AutoModelTagger) -> List[str]:
    """Segment a text into sentences using the senter model."""
    output = ""
    for char, label in senter(text):
        output += char
        if label in ["S", "E"]:
            output += "\n"
    return output.strip().split("\n")

def make_tasks(
    parser: Parser,
    senter: AutoModelTagger,
    stream: Iterable[DepExample],
) -> Iterator[DepExample]:
    """Pre-annotate with predicted dependencies and sentences from SuPaR."""
    examples = list(stream)
    texts = [eg["text"] for eg in examples]

    # segment into sentences; create a list of dict so that sentences can
    # be matched back to examples after batch parsing
    sentences = []
    for eg in examples:
        sentences.extend(
            [
                {
                    "work_id": f"{eg['meta']['zhengwen_id']}",
                    "doc_id": f"{eg['meta']['index']}",
                    "sentence_id": i + 1,
                    "sentence": sentence
                }
                for i, sentence in enumerate(segment_sentences(eg["text"], senter))
            ]
        )

    # batch parse all sentences and store their predictions
    predictions = parser.predict([[char for char in sentence] for sentence in sentences], lang=None)
    for sentence, prediction in zip(sentences, predictions):
        sentence["prediction"] = [
            {"head": head, "deprel": deprel} for head, deprel in
            zip(prediction.values[6], prediction.values[7])
        ]

    # rejoin sentences into examples and format as 
    for eg_sent, pred in zip(sentences, predictions.sentences):
        relations = []
        for child, (head, label) in enumerate(zip(pred.values[6], pred.values[7])):
            head = head - 1 if head else child
            relations.append({
                "head": head,
                "child": child,
                "label": label,
                "head_span": {
                    "start": head,
                    "end": head,
                    "token_start": head,
                    "token_end": head,
                },
                "child_span": {
                    "start": child,
                    "end": child,
                    "token_start": child,
                    "token_end": child,
                },
            })

        # TODO: use the 'flat' relation to preset the 'spans' key
        # then rework relations so that they are relative to the 'flat' spans

        eg["relations"] = relations
        eg = set_hashes(eg)
        yield eg

@prodigy.recipe(
    "suparkanbun.dep.correct",
    dataset=("Dataset to save annotations to", "positional", None, str),
    source=("Data to annotate (file path or '-' to read from standard input)", "positional", None, str),
    loader=("Loader (guessed from file extension if not set)", "option", "lo", str),
    labels=("Comma-separated relation label(s) to annotate or text file with one label per line", "option", "l", split_string),
    bert=("BERT model to use from SuPaR-Kanbun", "option", "b", str),
)
def dep_correct_suparkanbun(
    dataset: str,
    source: Union[str, Iterable[dict]],
    loader: Optional[str] = None,
    labels: List[str] = None,
    bert: str="roberta-classical-chinese-base-char"
) -> Dict[str, Any]:
    """Annotate dependency relations by correcting predictions from SuPaR-Kanbun."""
    # set up the tokenizer and BERT-based parser and senter
    nlp = spacy.blank("zh")
    parser = Parser.load(Path(DOWNLOAD_DIR) / f"{bert}.pos" / f"{bert}.supar")
    senter = AutoModelTagger(Path(DOWNLOAD_DIR) / f"{bert}.danku", SENT_TAGS)

    # stream in the data and add the model's predictions
    stream = get_stream(source, loader=loader, input_key="text")
    stream = add_tokens(nlp, stream)
    stream = make_tasks(parser, senter, stream)

    return {
        "dataset": dataset,
        "stream": stream,
        "view_id": "relations",
        "config": {
            "labels": UD,
            "relations_span_labels": labels,
        },
    }
