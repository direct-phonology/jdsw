import re
from typing import Callable

import pandas as pd

from .patterns import BLANK, WHITELIST, KR_ENTITY, MODE_HEADER, META_HEADER, LINE_BREAK, ANNOTATION


def filter_annotation(annotation: re.Match) -> str:
    """
    Filter out annotations that we can't convert into readings.

    If the annotation doesn't match a pattern in the whitelist, turn it into
    a blank. Leave matching annotations untouched.
    """

    if not any(annotype.match(annotation.group(0)) for annotype in WHITELIST):
        return f"{annotation.group('char')}\t{BLANK}"

    return annotation.group(0)


def fanqie_to_mc(annotation: re.Match, mc_table: pd.DataFrame) -> str:
    """
    Convert a fanqie (反) annotation into a Middle Chinese reading.

    Look up readings for the initial and rime characters in the annotation, then
    return the combination of their readings. If either of the initial or rime
    characters are missing or polyphonic, return a blank.
    """

    initial = mc_table[mc_table["char"] == annotation.group("initial")]
    rime = mc_table[mc_table["char"] == annotation.group("rime")]

    if initial.empty or rime.empty or len(initial) > 1 or len(rime) > 1:
        return f"{annotation.group('char')}\t{BLANK}"

    reading = "".join((initial["initial"].iloc[0], rime["rime"].iloc[0])).replace(
        "-", ""
    )

    return f"{annotation.group('char')}\t{reading}"


def yin_to_mc(annotation: re.Match, mc_table: pd.DataFrame) -> str:
    """
    Convert a 'yin' (音) annotation into a Middle Chinese reading.

    If the 'yin' character is monophonic (only one reading), and it's recorded
    in our data table, return that reading for the target character. Otherwise return a blank.
    """

    match = mc_table[mc_table["char"] == annotation.group("anno")]

    if match.empty or len(match) > 1:
        return f"{annotation.group('char')}\t{BLANK}"

    return f"{annotation.group('char')}\t{match['MC'].iloc[0]}"


def char_to_mc(annotation: re.Match, mc_table: pd.DataFrame) -> str:
    """
    Look up a Middle Chinese reading for a character.

    If the character is monophonic (only one reading), and it's recorded
    in our data table, return its reading. Otherwise return a blank.
    """

    match = mc_table[mc_table["char"] == annotation.group("char")]

    if match.empty or len(match) > 1:
        return f"{annotation.group('char')}\t{BLANK}"

    return f"{annotation.group('char')}\t{match['MC'].iloc[0]}"

def clean_text(text: str, to_unicode: Callable) -> str:
    """Clean an org-mode text and convert entities into unicode."""

    # replace kanripo entities with unicode placeholders
    text = KR_ENTITY.sub(to_unicode, text)

    # strip headers, page breaks, newlines, etc.
    text = MODE_HEADER.sub("", text)
    text = META_HEADER.sub("", text)
    text = LINE_BREAK.sub("\n", text)
    text = text.replace("¶", "")
    text = "".join(text.strip().splitlines())

    # some annotations were split across lines; we need to recombine them.
    # indicated by two consecutive annotations with no text between them
    text = text.replace(")(", "")

    # remove all remaining whitespace
    text = "".join(text.split())

    # remove line breaks within annotations, indicated by "/"
    text = text.replace("/", "")

    return text

def krp_entity_unicode(table: pd.DataFrame, match: re.Match) -> str:
    """Private use unicode representation for a Kanripo entity."""

    # entity will be either an id or a combo, we don't care which
    entity = match.group("id") or match.group("combo")

    # fetch from the table; warn if not found
    char = table.loc[table["form"] == entity]
    if char.empty:
        raise UserWarning(f"Kanripo entity not found: {entity}")

    return char["unicode"].values[0]

def split_text(text: str) -> str:
    """Reformat a text into a CoNLL-like format."""

    # split text by annotations; alternating char sequence with annotation
    chunks = ANNOTATION.split(text)
    chars, annos = chunks[::2], chunks[1::2]

    # all characters in sequence correspond to blanks except last, which matches
    # the annotation. each character on a new line, separated by tab
    fmt_chunks = zip(
        [f"\t{BLANK}\n".join(char) for char in chars],
        ["\t{}\n".format(anno) for anno in annos],
    )
    output = "".join(["".join(chunk) for chunk in fmt_chunks])

    # handle case where there's extra text after the last annotation
    if len(chars) > len(annos):
        output += "".join([f"{char}\t{BLANK}\n" for char in chars[-1]])

    return output

def reading_in_guangyun(char: str, reading: str) -> bool:
    """Check if the Guangyun lists a reading as valid for a character."""
    return False

def align_refs(text: str) -> str:
    """Realign phonetic annotations that are tied to the wrong character."""
    # split the text into char: annotation lines
    lines = [line.split("\t") for line in text.splitlines()]
    output = []

    # for each line:
    for i, (char, anno) in enumerate(lines):
        # check if the annotation portion is blank
        if anno == BLANK:
            # check up to 2 lines ahead for an annotation
            try:
                next_annos = [lines[i + 1][1], lines[i + 2][1]]
                next_annos = [a for a in next_annos if a != BLANK]
                next_anno = next_annos[0]
                # if any of those readings are valid for this char
                # per the GY, apply the first of the valid ones.

                # otherwise just use a blank

                # apply it to this character
                output.append((char, next_anno))
            except IndexError:
                output.append((char, BLANK))
        else:
            output.append((char, BLANK))

    # re-join lines and return
    return "\n".join(["\t".join(line) for line in output])
