#!/usr/bin/env python3

import re
from pathlib import Path
from typing import Callable

import pandas as pd
import typer
from tqdm import tqdm

# texts we don't care about using: paratextual material, notes, etc.
BLACKLIST = (
    "KR1g0003_000",  # introduction
    "KR1g0003_001",  # 序録
    "KR1g0003_031",  # notes
    "KR1g0003_032",  # notes
    "KR1g0003_033",  # notes
)

# artifacts in kanseki repository text
MODE_HEADER = re.compile(r"# -\*- mode: .+; -\*-\n")
META_HEADER = re.compile(r"#\+\w+: .+\n")
LINE_BREAK = re.compile(r"<pb:(?:.+)>¶\n")
ANNOTATION = re.compile(r"\((.+?)\)")

# fmt: off
KanripoEntity = re.compile(r"""
    (
    &(?P<id>KR\d+);     # entity with a code/id, e.g. &KR0001;
    |
    (?P<combo>\[.+?\])  # entity defined as a combo, e.g. [阿-可+利]
    )
""", re.VERBOSE)
# fmt: on


def krp_entity_unicode(table: pd.DataFrame, match: re.Match) -> str:
    """Private use unicode representation for a Kanripo entity."""

    # entity will be either an id or a combo, we don't care which
    entity = match.group("id") or match.group("combo")

    # fetch from the table; warn if not found
    char = table.loc[table["form"] == entity]
    if char.empty:
        raise UserWarning(f"Kanripo entity not found: {entity}")

    return char["unicode"].values[0]


def clean_text(text: str, to_unicode: Callable[[re.Match], str]) -> str:
    """Clean an org-mode text and convert entities into unicode."""

    # replace kanripo entities with unicode placeholders
    text = KanripoEntity.sub(to_unicode, text)

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


def split_text(text: str) -> str:
    """Reformat a text into a CoNLL-like format."""

    # split text by annotations; alternating char sequence with annotation
    chunks = ANNOTATION.split(text)
    chars, annos = chunks[::2], chunks[1::2]

    # all characters in sequence correspond to "_" except last, which matches
    # the annotation. each character on a new line, separated by tab
    fmt_chunks = zip(
        ["\t_\n".join(char) for char in chars],
        ["\t{}\n".format(anno) for anno in annos],
    )
    output = "".join(["".join(chunk) for chunk in fmt_chunks])

    # handle case where there's extra text after the last annotation
    if len(chars) > len(annos):
        output += "".join([f"{char}\t_\n" for char in chars[-1]])

    return output


def parse(in_dir: Path, out_dir: Path, unicode_table: Path) -> None:
    """Transform the Jingdian Shiwen text into raw text and annotations."""

    # read unicode conversion table
    unicode_table = pd.read_csv(
        unicode_table,
        sep="\t",
        names=["form", "unicode"],
    )
    to_unicode = lambda entity: krp_entity_unicode(unicode_table, entity)

    # clean out destination directory
    out_dir.mkdir(exist_ok=True)
    for file in out_dir.glob("*.txt"):
        file.unlink()

    # process source text
    for file in tqdm(sorted(list(in_dir.glob("*.txt")))):

        # ignore blacklisted material
        if any([file.stem in name for name in BLACKLIST]):
            continue

        # read the file and clean it
        text = clean_text(file.read_text(), to_unicode)

        # reformat conll-style
        text = split_text(text)

        # save the text into the output folder
        output = out_dir / f"{file.stem}.txt"
        output.open(mode="w").write(text)


if __name__ == "__main__":
    typer.run(parse)

__doc__ = parse.__doc__  # type: ignore
