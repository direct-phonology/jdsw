#!/usr/bin/env python3

import csv
import sys
from pathlib import Path

import typer
import pyconll

from scripts.lib.util import fuzzy_find


def main(zhengwen_file: Path, jdsw_file: Path, overwrite: bool = False) -> None:
    """
    TODO: write this

    $ alignjdsw jdsw/gongyang/001.csv sbck/gongyang/001.csv --overwrite
    """

    MAX_STACK_DEPTH = 5

    zhengwen = pyconll.load_from_file(zhengwen_file)

    # read JDSW edition into list of target:annotation tuples
    with open(jdsw_file, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        jdsw = [tuple(row.values()) for row in reader]


    phrase_ptr = 0
    sentence_ptr = 0
    text_ptr = 0
    min_sentence_ptr = 0

    # FIXME we're advancing the phrase pointer 
    while phrase_ptr < len(jdsw):
        phrase, annotation, *extra = jdsw[phrase_ptr]
        found = False
        sentence = zhengwen[sentence_ptr]
        while int(sentence.id.split(".")[1]) == 1:
            sentence = zhengwen[sentence_ptr]
            while text_ptr < len(sentence.text):
                loc = fuzzy_find(phrase, sentence.text[text_ptr:])
                if loc == -1:
                    sentence_ptr += 1
                    break
                else:
                    found = True
                    print(f"found {phrase}: in {sentence.text} ({sentence.id}.{text_ptr + loc}-{text_ptr + loc + len(phrase)})")
                    text_ptr += (loc + len(phrase))
                    phrase_ptr += 1
                    phrase, annotation, *extra = jdsw[phrase_ptr]
                    min_sentence_ptr = sentence_ptr
            text_ptr = 0
        sentence_ptr = min_sentence_ptr
        if not found:
            phrase_ptr += 1
            print(f"{phrase} not found")

    return zhengwen


if __name__ == "__main__":
    typer.run(main)

__doc__ = main.__doc__  # type: ignore
