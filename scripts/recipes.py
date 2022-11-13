from typing import Any, Dict, Iterable, List, Optional, Union
from pathlib import Path

import spacy
import prodigy
from suparkanbun import DOWNLOAD_DIR, AutoModelTagger
from prodigy.components.loaders import get_stream
from prodigy.components.preprocess import add_tokens
from prodigy.util import split_string, set_hashes

UPOS = {
    "ADJ", "ADP", "ADV", "AUX", "CCONJ", "DET", "INTJ", "NOUN", "NUM", "PART",
    "PRON", "PROPN", "PUNCT", "SCONJ", "SYM", "VERB", "X"
}

def make_tasks(tagger, stream, labels):
    """Add a 'spans' key to each example, with predicted POS."""
    texts = ((eg["text"], eg) for eg in stream)

    for text, eg in texts:
        spans = []
        for i, (_char, predictions) in enumerate(tagger(text)):
            # predictions look like "n,名詞,主体,書物,NOUN,Case=Tem"
            _xpos1, _xpos2, _xpos3, _xpos4, upos, _misc = predictions.split(",")
            
            # ignore if the predicted POS is not in the selected labels
            if labels and upos not in labels:
                continue

            # create a span dict for the predicted POS
            spans.append(
                {
                    "start": i,
                    "end": i,
                    "token_start": i,
                    "token_end": i,
                    "label": upos,
                }
            )
        
        # add to spans for the example and rehash it since we added data
        eg["spans"] = spans
        eg = set_hashes(eg)
        yield eg

@prodigy.recipe(
    "suparkanbun.pos.correct",
    dataset=("Dataset to save annotations to", "positional", None, str),
    source=("Data to annotate (file path or '-' to read from standard input)", "positional", None, str),
    loader=("Loader (guessed from file extension if not set)", "option", "lo", str),
    labels=("Comma-separated label(s) to annotate or text file with one label per line", "option", "l", split_string),
    bert=("BERT model to use from SuPaR-Kanbun", "option", "b", str),
)
def pos_correct_suparkanbun(
    dataset: str,
    source: Union[str, Iterable[dict]],
    loader: Optional[str] = None,
    labels: Optional[List[str]] = None,
    bert: str="roberta-classical-chinese-base-char"
) -> Dict[str, Any]:
    """Annotate POS tags by correcting predictions from SuPaR-Kanbun."""
    # set up the tokenizer and BERT-based tagger
    nlp = spacy.blank("och")
    labels = labels or list(UPOS)
    tagger_labels = (Path(DOWNLOAD_DIR) / "labelPOS.txt").read_text().strip().splitlines()
    tagger = AutoModelTagger(Path(DOWNLOAD_DIR) / f"{bert}.pos", tagger_labels)

    # stream in the data and add predicted POS tags
    stream = get_stream(source, loader=loader, input_key="text")
    stream = add_tokens(nlp, stream)
    stream = make_tasks(tagger, stream, labels)

    return {
        "dataset": dataset,
        "stream": stream,
        "view_id": "pos_manual",
        "config": {
            "lang": nlp.lang,
            "labels": labels,
            "exclude_by": "input",
            "auto_count_stream": True,
        },
    }
