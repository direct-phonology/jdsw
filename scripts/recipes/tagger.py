from typing import Any, Dict, Iterable, List, Optional, Union, Iterator, Container
from pathlib import Path

import spacy
import prodigy
from spacy.language import Language
from spacy.matcher import Matcher
from suparkanbun import DOWNLOAD_DIR, AutoModelTagger
from prodigy.components.loaders import get_stream
from prodigy.components.preprocess import add_tokens
from prodigy.util import split_string, set_hashes
from prodigy.types import PosExample

UPOS = [
    "SYM", "X", "PROPN", "VERB", "NOUN", "ADP", "PART", "PRON", "AUX", "DET",
    "ADJ", "ADV", "CCONJ", "SCONJ", "INTJ", "NUM", "PUNCT"
]

PATTERNS: Dict[str, Dict[str, List]] = {
    "fanqie": {
        "patterns": [[{}, {}, {"TEXT": "反"}]],
        "outputs": ["X", "X", "VERB"],
    },
    "yin": {
        "patterns": [[{"TEXT": "音"}, {}]],
        "outputs": ["VERB", "X"],
    },
    "variant": {
        "patterns": [[{"TEXT": "作"}, {}]],
        "outputs": ["VERB", "SYM"],
    }
}

def make_tasks(
    nlp: Language,
    tagger: AutoModelTagger,
    stream: Iterable[PosExample],
    labels: Container[str],
) -> Iterator[PosExample]:
    """Add a 'spans' key to each example, with predicted POS."""
    texts = ((eg["text"], eg) for eg in stream)
    matcher = Matcher(nlp.vocab)
    for match_id, config in PATTERNS.items():
        matcher.add(match_id, config["patterns"])

    for text, eg in texts:
        spans: List[Dict[str, str | int]] = [{
            "start": i,
            "end": i,
            "token_start": i,
            "token_end": i,
        } for i in range(len(text))]

        # make a first pass to pre-annotate any provided patterns
        doc = nlp(text)
        for match_id, start, end in matcher(doc):   # type: ignore
            string_id = str(nlp.vocab.strings[match_id])
            outputs: List[str] = PATTERNS[string_id]["outputs"]
            for i, c in enumerate(range(start, end)):
                spans[c]["label"] = outputs[i]

        # make a second pass to add predictions for all other tokens
        for i, (_char, predictions) in enumerate(tagger(text)):

            # predictions look like "n,名詞,主体,書物,NOUN,Case=Tem"
            _xpos1, _xpos2, _xpos3, _xpos4, upos, _misc = predictions.split(",")
            
            # ignore if the predicted POS is not in the selected labels
            if upos not in labels:
                continue

            # use the predicted POS if we didn't have one from a pattern
            spans[i]["label"] = spans[i].get("label", upos)
        
        # add to spans for the example and rehash it since we added data
        eg["spans"] = spans
        eg = set_hashes(eg)
        yield eg

@prodigy.recipe(
    "suparkanbun.pos.correct",
    dataset=("Dataset to save annotations to", "positional", None, str),
    source=("Data to annotate (file path or '-' to read from standard input)", "positional", None, str),
    loader=("Loader (guessed from file extension if not set)", "option", "lo", str),
    labels=("Comma-separated POS label(s) to annotate or text file with one label per line", "option", "l", split_string),
    bert=("BERT model to use from SuPaR-Kanbun", "option", "b", str),
)
def pos_correct_suparkanbun(
    dataset: str,
    source: Union[str, Iterable[dict]],
    loader: Optional[str] = None,
    labels: Container[str] = UPOS,
    bert: str="roberta-classical-chinese-base-char"
) -> Dict[str, Any]:
    """Annotate POS tags by correcting predictions from SuPaR-Kanbun."""
    # set up the tokenizer and BERT-based tagger
    nlp = spacy.blank("och")
    tagger_labels = (Path(DOWNLOAD_DIR) / "labelPOS.txt").read_text().strip().splitlines()
    tagger = AutoModelTagger(Path(DOWNLOAD_DIR) / f"{bert}.pos", tagger_labels)

    # stream in the data and add predicted POS tags
    stream = get_stream(source, loader=loader, input_key="text")
    stream = add_tokens(nlp, stream)
    stream = make_tasks(nlp, tagger, stream, labels)

    return {
        "dataset": dataset,
        "stream": stream,
        "view_id": "pos_manual",
        "config": {
            "labels": labels,
        },
    }
