import re
from pathlib import Path
import json

import pandas as pd
import spacy

from .patterns import (
    BLANK,
    EMPTY_ANNO,
    FANQIE,
    YIN,
    KR_ENTITY,
    MODE_HEADER,
    META_HEADER,
    PAGE_BREAK,
    ANNOTATION,
    COMMENT,
)
from .phonology import Reconstruction, NoReadingError, MultipleReadingsError

KR_UNICODE = pd.read_csv(Path("data/kr-unicode.csv"))
MC_BAXTER = Reconstruction(pd.read_csv(Path("data/GDR-SBGY-full.csv")))
OC_BAXTER = NotImplementedError("TODO")
VARIANT_TABLE = str.maketrans(json.loads(Path("data/variants.json").read_text()))

NLP = spacy.blank("och")
NLP.add_pipe("sentencizer")


def get_org_metadata(text: str) -> dict:
    """Extract metadata from an org-mode text."""
    metadata = {}
    for header in META_HEADER.finditer(text):
        key, value = header.group("key"), header.group("value")
        if key == "PROPERTY":
            key, value = value.split(" ", 1)
        if "," in value:
            value = value.split(",")
        metadata[key.lower()] = value
    return metadata


def clean_org_text(text: str) -> str:
    """Remove org-mode artifacts in Kanseki repository text."""
    text = MODE_HEADER.sub("", text)
    text = META_HEADER.sub("", text)
    text = PAGE_BREAK.sub("", text)
    text = COMMENT.sub("", text)
    return text


def clean_sbck_text(text: str) -> str:
    """Clean an SBCK text"""
    # remove pilcrows
    text = text.replace("¶", "")

    # remove line breaks
    text = "".join(text.strip().splitlines())

    # some annotations were split across lines; we need to recombine them.
    # indicated by two consecutive annotations with no text between them
    text = text.replace(")(", "")

    # remove all remaining whitespace
    text = "".join(text.split())

    # remove slashes inside annotations
    text = text.replace("/", "")

    return text


def krp_entity_unicode(match: re.Match) -> str:
    """Private use unicode representation for a Kanripo entity."""

    # entity will be either an id or a combo, we don't care which
    entity = match.group("id") or match.group("combo")

    # fetch from the table; warn if not found
    char = KR_UNICODE.loc[KR_UNICODE["form"] == entity]
    if char.empty:
        raise UserWarning(f"Kanripo entity not found: {entity}")

    return char["unicode"].values[0]


def convert_krp_entities(text: str) -> str:
    """Convert all Kanripo entities to unicode."""
    return KR_ENTITY.sub(krp_entity_unicode, text)


def split_text(text: str, sep: str = "\t", by_char: bool = True) -> str:
    """
    Reformat a text into a tabular form with annotations opposite text.

    If by_char is True (the default), each character will get its own line,
    similar to ConLL-2002 format, and the annotation will be opposite the
    last character in each sequence. Otherwise, each line will be a sequence of characters, with the corresponding annotation opposite it.

    Sep is set to the tab character by default to produce CoNLL-2002 output, but
    can be changed to a comma to produce .csv output.
    """

    # split text by annotations; alternating char sequence with annotation
    chunks = ANNOTATION.split(text)
    chars, annos = chunks[::2], chunks[1::2]

    # all characters in sequence correspond to blanks except last, which matches
    # the annotation. each character on a new line, separated by separator
    fmt_chunks = zip(
        [f"{sep}{BLANK}\n".join(char) for char in chars] if by_char else chars,
        [f"{sep}{anno}\n" for anno in annos],
    )
    output = "".join(["".join(chunk) for chunk in fmt_chunks])

    # handle case where there's extra text after the last annotation
    if len(chars) > len(annos) and chars[-1]:
        output += "".join(
            [f"{char}{sep}{BLANK}\n" for char in chars[-1]]
            if by_char
            else f"{chars[-1]}{sep}"
        )

    return output


def align_refs(text: str, rc: Reconstruction, lookahead: int = 2) -> str:
    """Realign phonetic annotations that are tied to the wrong character."""
    # split the text into char: annotation lines
    lines = [line.split("\t") for line in text.splitlines()]
    output = []

    # for each line:
    for i, (char, anno) in enumerate(lines):
        # check if the annotation portion is blank
        if anno == BLANK:
            # check up to max_lookahead lines ahead for an annotation
            next_annos = [(char, line[1]) for line in lines[i + 1 : i + 1 + lookahead]]
            # if any did have an annotation, check if valid per Guangyun
            next_annos = list(filter(lambda l: rc.is_valid_reading(*l), next_annos))
            # use the first of the valid annotations
            if next_annos:
                output.append((char, next_annos[0][1]))
            else:
                output.append((char, BLANK))
        # if there was an annotation but it's invalid, blank it instead
        else:
            if rc.is_valid_reading(char, anno):
                output.append((char, anno))
            else:
                output.append((char, BLANK))

    # re-join lines and return
    return "\n".join(["\t".join(line) for line in output])


def split_sentences(text: str) -> list:
    """Split a text into sentences."""

    # use spacy's sentencizer
    doc = NLP(text)
    return [sent.text for sent in doc.sents]


def strip_punctuation(text: str) -> str:
    """Remove punctuation from a text."""

    # use the spacy model to detect punctuation
    doc = NLP(text)
    return "".join([token.text for token in doc if not token.is_punct])


def convert_fanqie(text: str, rc: Reconstruction, stats: dict) -> str:
    """Convert fanqie annotations into Middle Chinese transcriptions."""

    def _convert(annotation: re.Match) -> str:
        try:
            reading = rc.fanqie_reading_for(
                annotation.group("initial"), annotation.group("rime")
            )
            return f"{annotation.group('char')}\t{reading}"
        except (NoReadingError, MultipleReadingsError) as e:
            stats["errors"][str(e)] += 1
            return f"{annotation.group('char')}\t{BLANK}"

    return FANQIE.sub(_convert, text)


def convert_yin(text: str, rc: Reconstruction, stats: dict) -> str:
    """Convert yin annotations into Middle Chinese transcriptions."""

    def _convert(annotation: re.Match) -> str:
        try:
            reading = rc.reading_for(annotation.group("char"))
            return f"{annotation.group('char')}\t{reading}"
        except (NoReadingError, MultipleReadingsError) as e:
            stats["errors"][str(e)] += 1
            return f"{annotation.group('char')}\t{BLANK}"

    return YIN.sub(_convert, text)


def augment_annotations(text: str, rc: Reconstruction, stats: dict) -> str:
    """Add annotations from the Guangyun for monophonic characters."""

    def _convert(annotation: re.Match) -> str:
        try:
            reading = rc.reading_for(annotation.group("char"))
            return f"{annotation.group('char')}\t{reading}"
        except (NoReadingError, MultipleReadingsError) as e:
            stats["errors"][str(e)] += 1
            return f"{annotation.group('char')}\t{BLANK}"

    return EMPTY_ANNO.sub(_convert, text)


def fuzzy_find(phrase: str, text: str) -> int:
    """True if phrase is found in text, ignoring variant characters."""

    # collapse variants into a single character
    # TODO: use levenshtein for distance matching
    text_norm = text.translate(VARIANT_TABLE)
    phrase_norm = phrase.translate(VARIANT_TABLE)

    return text_norm.find(phrase_norm)
