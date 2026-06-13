#!/usr/bin/env python3

from collections import Counter
from pathlib import Path

import pandas as pd
import srsly
import typer

from scripts.lib.corpus import doc_for, group_annotations, load_clean_docs, load_juan_map
from scripts.lib.phonology import Reconstruction
from scripts.lib.polyphone import polyphone_records
from scripts.lib.ruzi import DEFAULT_PROFILE_PATH, DefaultReadings


def main(
    annotations_file: Path = Path("assets/annotations.jsonl"),
    source_path: Path = Path("txt/sbck"),
    juan_file: Path = Path("assets/juan.csv"),
    output_file: Path = Path("data/polyphones.jsonl"),
    readings_file: Path = Path("assets/GDR-SBGY-full.csv"),
    profiles_file: Path = DEFAULT_PROFILE_PATH,
    context: int = 24,
) -> None:
    """
    Export polyphone disambiguation data from aligned JDSW annotations.

    Aligns the headwords of each JDSW sub-juan's annotations against the SBCK
    commentary edition it comments on (mapped via juan.csv), with edition
    layers tracked so each record carries a main/commentary label. Editions
    are expected as Kanripo clones under source_path, pinned to the branch
    recorded in docs.csv (sbck_branch). Extracts fanqie/duruo readings,
    resolves 如字 to default readings (when profiles_file is present), expands
    下同/注同 scope, validates against the Guangyun, and writes one JSON-lines
    record per (character in context, reading) pair.
    """
    rc = Reconstruction(pd.read_csv(readings_file))
    default_readings = DefaultReadings.from_csv(profiles_file)

    juan_map = load_juan_map(juan_file)
    by_juan = group_annotations(srsly.read_jsonl(annotations_file), juan_map)
    docs = load_clean_docs(source_path)

    stats: Counter = Counter()
    records = []
    for source_id, entries in sorted(by_juan.items()):
        doc = doc_for(source_id, docs)
        if doc is None:
            stats["juan missing"] += 1
            continue
        stats["juan aligned"] += 1
        for record in polyphone_records(
            entries, doc.text, rc, context=context, layers=doc.meta.get("layers"),
            default_readings=default_readings,
        ):
            records.append(record)
            stats[f"kind: {record['kind']}"] += 1
            stats[f"validation: {record['validation']}"] += 1
            stats[f"layer: {record['layer']}"] += 1

    srsly.write_jsonl(output_file, records)

    typer.echo(f"{len(records)} records written to {output_file}", err=True)
    for key, count in sorted(stats.items()):
        typer.echo(f"  {key}: {count}", err=True)


if __name__ == "__main__":
    typer.run(main)

__doc__ = main.__doc__  # type: ignore
