#!/usr/bin/env python3

import pathlib

import typer

from lib.util import clean_sbck_text, clean_org_text, split_text, convert_krp_entities


def main(file: pathlib.Path, headers: bool=False) -> None:
    """
    Parse a SBCK edition text into base text and annotations/commentary.

    Outputs a .csv representation to stdout, where each unbroken sequence of 
    characters is separated by a comma from its annotation or commentary, one 
    pair per line.

    If headers is True, the first line will be a header with the column names.
    """

    # read input file
    text = file.read_text(encoding="utf-8")

    # clean all artifacts from text
    text = convert_krp_entities(text)
    text = clean_org_text(text)
    text = clean_sbck_text(text)

    # split into comma-separated source:annotation lines
    text = split_text(text, sep=",", by_char=False)

    # write to stdout
    if headers:
        typer.echo("source,commentary")
    typer.echo(text.strip())


if __name__ == "__main__":
    typer.run(main)

__doc__ = main.__doc__  # type: ignore
