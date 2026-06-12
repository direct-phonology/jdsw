#!/usr/bin/env python3

from collections import Counter
from pathlib import Path

import srsly
import typer

from scripts.lib.alignment import DAMAGED, PARTIAL, align_sequence, alternate_graphs
from scripts.lib.corpus import doc_for, group_annotations, load_clean_docs, load_juan_map
from scripts.lib.variants import normalize


def candidate_pairs(lemma: str, span: str, verified_head: bool) -> list[tuple[str, str]]:
    """
    (lemma char, text char) pairs in the unverified region of a partial match.

    A prefix-verified partial aligns the lemma and span from the left, a
    suffix-verified one from the right; characters already equated by the
    variant tables (or hidden by a damaged-char placeholder) are skipped, so
    what remains are exactly the unexplained graph differences.
    """
    n = min(len(lemma), len(span))
    indices = range(n) if verified_head else range(-1, -n - 1, -1)
    return [
        (lemma[i], span[i])
        for i in indices
        if span[i] != DAMAGED and normalize(lemma[i]) != normalize(span[i])
    ]


def main(
    annotations_file: Path = Path("assets/annotations.jsonl"),
    source_path: Path = Path("txt/sbck"),
    juan_file: Path = Path("assets/juan.csv"),
    output_file: Path = Path("data/variant_candidates.jsonl"),
    min_count: int = 2,
) -> None:
    """
    Propose variants.json candidates from partial alignment matches.

    Partial matches are the variant-harvesting queue (see docs/corpus.md): a
    partial usually means the lemma's graph differs from the witness's at one
    position. Aligns every juan against its SBCK edition, diffs each partial
    span against its lemma, and writes character pairs not already equated by
    variants.json/normalization.json, most frequent first. Pairs are
    candidates, not conclusions — vet them before adding to variants.json.
    """
    juan_map = load_juan_map(juan_file)
    by_juan = group_annotations(srsly.read_jsonl(annotations_file), juan_map)
    docs = load_clean_docs(source_path)

    counts: Counter = Counter()
    examples: dict[tuple[str, str], dict] = {}
    for source_id, entries in sorted(by_juan.items()):
        doc = doc_for(source_id, docs)
        if doc is None:
            continue
        lemmas = [entry["meta"]["headword"] for entry in entries]
        alternates = [alternate_graphs(entry["text"]) for entry in entries]
        for match in align_sequence(lemmas, doc.text, alternates=alternates):
            if match.confidence != PARTIAL:
                continue
            span = doc.text[match.start : match.end]
            verified_head = match.verified_end != match.end
            for pair in candidate_pairs(match.lemma, span, verified_head):
                counts[pair] += 1
                examples.setdefault(
                    pair, {"lemma": match.lemma, "span": span, "juan": source_id}
                )

    records = [
        {"lemma_char": a, "text_char": b, "count": count, **examples[(a, b)]}
        for (a, b), count in counts.most_common()
        if count >= min_count
    ]
    srsly.write_jsonl(output_file, records)

    typer.echo(f"{len(records)} candidate pairs written to {output_file}", err=True)
    for record in records[:20]:
        typer.echo(
            f"  {record['lemma_char']} ~ {record['text_char']} ×{record['count']}"
            f" ({record['lemma']} / {record['span']}, {record['juan']})",
            err=True,
        )


if __name__ == "__main__":
    typer.run(main)

__doc__ = main.__doc__  # type: ignore
