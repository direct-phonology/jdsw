#!/usr/bin/env python3

from pathlib import Path
import re
import subprocess

import typer


def main(in_dir: Path, out_dir: Path) -> None:
    """
    Run sbck2tsv all files in the input directory and map them to corresponding
    files in the output directory.
    """

    # only process files that end in a 3-digit suffix
    for file in in_dir.glob("**/*.txt"):
        if re.match(r".+_\d{3}$", file.stem):

            # make sure output directory exists
            out_file = Path(out_dir, file.stem).with_suffix(".tsv")
            out_file.parent.mkdir(parents=True, exist_ok=True)

            # call bin/sbck2tsv
            subprocess.run(
                [Path("bin/sbck2tsv"), file],
                stdout=out_file.open("w", encoding="utf-8"),
            )

            # print the name of the file when finished
            typer.echo(file, err=True)


if __name__ == "__main__":
    typer.run(main)

__doc__ = main.__doc__  # type: ignore
