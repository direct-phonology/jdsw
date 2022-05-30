#!/usr/bin/env python3

from pathlib import Path
import re
import subprocess

import typer


def main(jdsw_path: Path, sbck_path: Path) -> None:
    """
    Run alignjdsw recursively on all files in the input directory and overwrite.

    First param is the JDSW directory; second is the SBCK directory.
    """

    # only process files that end in a 3-digit suffix
    for file in jdsw_path.glob("**/*.txt"):
        if re.match(r"^\d{3}$", file.stem):
            # look for corresponding file in SBCK directory; skip if none
            sbck_file = Path(sbck_path, *file.parts[2:])
            if not sbck_file.exists():
                continue

            # call bin/alignjdsw and overwrite the input file
            subprocess.run(
                [Path("bin/alignjdsw"), file, sbck_file, "--overwrite"],
            )

            # print the name of the file when finished
            typer.echo(file, err=True)


if __name__ == "__main__":
    typer.run(main)

__doc__ = main.__doc__  # type: ignore
