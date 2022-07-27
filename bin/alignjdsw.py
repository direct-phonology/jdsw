#!/usr/bin/env python3

import csv
import sys
from pathlib import Path

import typer

from lib.patterns import BLANK


def main(jdsw_file: Path, sbck_file: Path, overwrite: bool = False) -> None:
    """
    Compare the JDSW edition of a text with the SBCK edition of the same text.

    Annotations in the JDSW edition that correspond to the source text in the
    SBCK edition are noted as 'source', while those that correspond to the
    commentary are noted as 'commentary' in a new column. Annotations that don't
    appear to map onto anywhere in the SBCK edition will have a blank. Output
    is written to stdout or, optionally, to overwrite the JDSW input file.

    $ alignjdsw jdsw/gongyang/001.csv sbck/gongyang/001.csv --overwrite
    """

    # read JDSW edition into list of target:annotation tuples
    with open(jdsw_file, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        jdsw = [tuple(row.values()) for row in reader]

    # read SBCK edition into list of source:commentary tuples and original text
    with open(sbck_file, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        sbck = [tuple(row.values()) for row in reader]
        sbck_text = "".join(["".join(row[:2]) for row in sbck])

    # construct a map of the SBCK edition where each character index is mapped
    # to a boolean indicating whether that character is in the source text
    sbck_map = []
    for source, commentary, *extra in sbck:
        sbck_map += [True for c in source]
        sbck_map += [False for c in commentary]
    assert len(sbck_map) == len(sbck_text)

    # use a pointer into the full SBCK text to find the next possible place an
    # annotation from the JDSW could apply. if the annotation target is in the
    # source text, we advance the pointer and keep that annotation. if the
    # annotation target is in the commentary, we advance the pointer and
    # ignore the annotation. if the target isn't found, log it.
    output: list[dict[str, str]] = []
    pointer = 0
    for target, annotation, *extra in jdsw:
        remaining = sbck_text[pointer:]
        location = remaining.find(target)
        if location == -1:
            output.append({
                "source": target,
                "commentary": annotation,
                "location": BLANK,
            })
        else:
            pointer = location
            if sbck_map[location] is True:
                output.append({
                    "source": target,
                    "commentary": annotation,
                    "location": "source",
                })
            else:
                output.append({
                    "source": target,
                    "commentary": annotation,
                    "location": "commentary",
                })

    # overwrite input JDSW file if requested, otherwise write to stdout
    if overwrite:
        with open(jdsw_file, "w", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["source", "commentary", "location"])
    else:
        writer = csv.DictWriter(sys.stdout, fieldnames=["source", "commentary", "location"])
    writer.writeheader()
    writer.writerows(output)


if __name__ == "__main__":
    typer.run(main)

__doc__ = main.__doc__  # type: ignore
