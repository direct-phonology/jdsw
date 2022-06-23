#!/usr/bin/env python3

import pathlib

import typer

from lib.util import clean_sbck_text, clean_org_text, split_text, convert_krp_entities


def main(file: pathlib.Path) -> None:
    """
    Parse a SBCK edition text into base text and annotations/commentary.

    Outputs a .conll-like representation to stdout, where each unbroken
    sequence of characters is separated by a tab from its annotation or
    commentary, one pair per line.
    """

    # read input file
    text = file.read_text(encoding="utf-8")

    # clean all artifacts from text
    text = convert_krp_entities(text)
    text = clean_org_text(text)
    text = clean_sbck_text(text)

    # split into tab-separated source:annotation lines
    text = split_text(text, by_char=False)

    # write to stdout
    typer.echo(text.strip())


if __name__ == "__main__":
    typer.run(main)

__doc__ = main.__doc__  # type: ignore
