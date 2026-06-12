#!/usr/bin/env python3

from pathlib import Path

import srsly
import typer


def main(annotations_file: Path = Path("assets/annotations.jsonl")) -> None:
    """
    Add a global sequence number to the annotations corpus.

    The index field restarts per JDSW physical sub-juan, while juan_id tracks
    the commented work's chapters — so whenever a chapter spans a JDSW 卷
    boundary, sorting by (juan_id, index) interleaves multiple lemma sequences
    and breaks the monotonic ordering that alignment depends on. The correct
    order is (jdsw_id, index); this script sorts by it and writes the result
    back with an explicit meta.sequence so consumers don't have to know.
    """
    entries = list(srsly.read_jsonl(annotations_file))
    entries.sort(key=lambda entry: (entry["meta"]["jdsw_id"], entry["meta"]["index"]))
    for sequence, entry in enumerate(entries):
        entry["meta"]["sequence"] = sequence
    srsly.write_jsonl(annotations_file, entries)
    typer.echo(f"sequenced {len(entries)} annotations in {annotations_file}", err=True)


if __name__ == "__main__":
    typer.run(main)

__doc__ = main.__doc__  # type: ignore
