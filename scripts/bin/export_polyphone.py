#!/usr/bin/env python3

from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd
import srsly
import typer

from scripts.lib.loaders import KanripoTxtDataset
from scripts.lib.phonology import Reconstruction
from scripts.lib.polyphone import polyphone_records


def main(
    annotations_file: Path = Path("assets/annotations.jsonl"),
    zhengwen_path: Path = Path("txt/zhengwen"),
    output_file: Path = Path("data/polyphones.jsonl"),
    readings_file: Path = Path("assets/GDR-SBGY-full.csv"),
    context: int = 24,
) -> None:
    """
    Export polyphone disambiguation data from aligned JDSW annotations.

    Aligns the headwords of each juan's annotations against its zhengwen text,
    extracts fanqie/duruo readings, validates them against the Guangyun, and
    writes one JSON-lines record per (character in context, reading) pair.
    """
    rc = Reconstruction(pd.read_csv(readings_file))

    # group annotation entries by the zhengwen juan they comment on.
    # index restarts per JDSW physical sub-juan, so sorting by it alone
    # interleaves lemma sequences whenever a chapter spans a 卷 boundary
    # and silently breaks the monotonicity that alignment depends on;
    # (jdsw_id, index) is the correct global order
    by_juan: dict[str, list[dict]] = defaultdict(list)
    for entry in srsly.read_jsonl(annotations_file):
        by_juan[entry["meta"]["zhengwen_id"]].append(entry)
    for entries in by_juan.values():
        entries.sort(key=lambda e: (e["meta"]["jdsw_id"], e["meta"]["index"]))

    docs = {doc.id: doc for doc in KanripoTxtDataset(zhengwen_path)}

    stats: Counter = Counter()
    records = []
    for zhengwen_id, entries in sorted(by_juan.items()):
        doc = docs.get(zhengwen_id)
        if doc is None:
            stats["juan missing"] += 1
            continue
        stats["juan aligned"] += 1
        for record in polyphone_records(
            entries, doc.text, rc, context=context, layers=doc.meta.get("layers")
        ):
            records.append(record)
            stats[f"alignment: {record['alignment']}"] += 1
            stats[f"validation: {record['validation']}"] += 1

    srsly.write_jsonl(output_file, records)

    typer.echo(f"{len(records)} records written to {output_file}", err=True)
    for key, count in sorted(stats.items()):
        typer.echo(f"  {key}: {count}", err=True)


if __name__ == "__main__":
    typer.run(main)

__doc__ = main.__doc__  # type: ignore
