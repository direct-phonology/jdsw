#!/usr/bin/env python3

import csv
import sys
from pathlib import Path

import typer


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
    # annotation from the JDSW could apply. note whether it appears in the
    # source, commentary, or isn't found at all.
    output: list[dict[str, str]] = []
    pointer = 0
    for target, annotation, *extra in jdsw:
        remaining = sbck_text[pointer:]
        location = remaining.find(target)
        if location == -1:  # not found
            output.append(
                {
                    "source": target,
                    "commentary": annotation,
                    "location": "unknown",
                }
            )
        else:
            if sbck_map[pointer + location] is True:  # in source
                output.append(
                    {
                        "source": target,
                        "commentary": annotation,
                        "location": "source",
                    }
                )
            else:  # in commentary
                output.append(
                    {
                        "source": target,
                        "commentary": annotation,
                        "location": "commentary",
                    }
                )
            pointer = pointer + location + len(target)

    # overwrite input JDSW file if requested, otherwise write to stdout
    if overwrite:
        with open(jdsw_file, "w", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["source", "commentary", "location"])
    else:
        writer = csv.DictWriter(
            sys.stdout, fieldnames=["source", "commentary", "location"]
        )
    writer.writeheader()
    writer.writerows(output)


if __name__ == "__main__":
    typer.run(main)

__doc__ = main.__doc__  # type: ignore
