#!/usr/bin/env python3

import typer
import spacy
import sys

from scripts.lib.components import doc_spans_jdsw


def main() -> None:
    """Predict spans for the given text."""
    nlp = spacy.blank("zh")
    text = sys.stdin.read()
    doc = nlp.make_doc(text)
    for span in doc_spans_jdsw(doc):
        print(span.label_, span.text, sep="\t")


if __name__ == "__main__":
    typer.run(main)

__doc__ = main.__doc__
