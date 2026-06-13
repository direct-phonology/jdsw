#!/usr/bin/env python3

"""
Align the full JDSW annotations corpus against the SBCK source editions,
per work (see docs/corpus.md). The per-juan grouping keyed by juan.csv routes
most multi-卷 annotations to a fascicle that has no file; aligning per work —
merging a work's fascicles into one text and aligning its whole headword
sequence in global meta.sequence order — is monotonic and reproduces the
per-work match rates recorded in docs/corpus.md (~95.6% overall).
"""

import csv
import subprocess
from collections import Counter
from pathlib import Path

import srsly
import typer

from scripts.lib.alignment import (
    ALTERNATE,
    ANCHOR,
    GAP,
    PARTIAL,
    align_sequence,
    alternate_graphs,
    layer_at,
)
from scripts.lib.corpus import doc_for, group_by_work, load_clean_docs

app = typer.Typer()

MATCHED = (ANCHOR, GAP, ALTERNATE, PARTIAL)
KANRIPO = "https://github.com/kanripo"


@app.command("fetch-sources")
def fetch_sources(
    source_path: Path = Path("txt/sbck"),
    docs_csv: Path = Path("assets/docs.csv"),
) -> None:
    """
    Clone each SBCK source edition listed in docs.csv into source_path.

    Branch pinning is mandatory: the default branch of each Kanripo repo is the
    bare HFL witness and lacks the commentary the JDSW glosses, so each repo is
    cloned at the branch recorded in docs.csv (sbck_branch). docs.csv stays the
    single source of truth for which edition and branch each work uses.
    """
    for row in csv.DictReader(open(docs_csv, encoding="utf-8")):
        sbck_id, branch = row["sbck_id"], row["sbck_branch"]
        dest = source_path / sbck_id
        if dest.exists():
            typer.echo(f"skip {sbck_id} (already at {dest})", err=True)
            continue
        typer.echo(f"clone {sbck_id} @ {branch} -> {dest}", err=True)
        subprocess.run(
            ["git", "clone", "-b", branch, f"{KANRIPO}/{sbck_id}", str(dest)],
            check=True,
        )


@app.command("align")
def align(
    source_path: Path = Path("txt/sbck"),
    annotations: Path = Path("assets/annotations.jsonl"),
    out: Path = Path("data/aligned.jsonl"),
    metrics: Path = Path("metrics/alignment.json"),
    docs_csv: Path = Path("assets/docs.csv"),
) -> None:
    """
    Align the annotations corpus per work and write one record per annotation.

    Each record carries the matched span, the alignment confidence, the edition
    layer at the match (main/commentary/unknown), and the annotation's source
    meta. Per-work and overall confidence counts plus the matched rate are
    written to the metrics file and printed to stderr.
    """
    docs = load_clean_docs(source_path)
    entries = list(srsly.read_jsonl(annotations))
    by_work = group_by_work(entries, docs_csv)

    records: list[dict] = []
    per_work: dict[str, Counter] = {}
    skipped: list[str] = []

    for work_id in sorted(by_work):
        group = by_work[work_id]
        doc = doc_for(work_id, docs)
        if doc is None:
            skipped.append(work_id)
            typer.echo(f"skip {work_id}: no source doc ({len(group)} annotations)", err=True)
            continue

        layers = doc.meta.get("layers", [])
        headwords = [e["meta"]["headword"] for e in group]
        alternates = [alternate_graphs(e["text"]) for e in group]
        matches = align_sequence(headwords, doc.text, alternates=alternates)

        counts: Counter = Counter()
        for entry, match in zip(group, matches):
            counts[match.confidence] += 1
            records.append(
                {
                    "lemma": match.lemma,
                    "x_span": [match.start, match.end] if match.found else None,
                    "confidence": match.confidence,
                    "layer": layer_at(layers, match.start) if match.found else None,
                    "source_id": work_id,
                    "meta": entry["meta"],
                }
            )
        per_work[work_id] = counts

    overall: Counter = Counter()
    for counts in per_work.values():
        overall.update(counts)

    report = {
        "overall": _summary(overall),
        "works": {work_id: _summary(c) for work_id, c in per_work.items()},
        "skipped": skipped,
    }

    out.parent.mkdir(parents=True, exist_ok=True)
    metrics.parent.mkdir(parents=True, exist_ok=True)
    srsly.write_jsonl(out, records)
    srsly.write_json(metrics, report)

    _print_table(report)


def _summary(counts: Counter) -> dict:
    total = sum(counts.values())
    matched = sum(counts[c] for c in MATCHED)
    return {
        "total": total,
        "matched": matched,
        "matched_rate": matched / total if total else 0.0,
        "confidence": dict(counts),
    }


def _print_table(report: dict) -> None:
    typer.echo(f"{'work':<14}{'n':>7}{'matched':>9}{'rate':>8}", err=True)
    for work_id, summary in sorted(report["works"].items()):
        typer.echo(
            f"{work_id:<14}{summary['total']:>7}{summary['matched']:>9}"
            f"{summary['matched_rate']:>8.1%}",
            err=True,
        )
    overall = report["overall"]
    typer.echo(
        f"{'OVERALL':<14}{overall['total']:>7}{overall['matched']:>9}"
        f"{overall['matched_rate']:>8.1%}",
        err=True,
    )


if __name__ == "__main__":
    app()
