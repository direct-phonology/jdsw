"""
Shared helpers for aligning annotations.jsonl against source editions.

The source of truth for which edition each JDSW sub-juan comments on is
assets/juan.csv (juan level) and assets/docs.csv (work level, including the
Kanripo branch to clone — see docs/corpus.md on why the branch must be
pinned). Texts are expected as Kanripo clones under a local directory,
one work per subdirectory, e.g.:

    git clone -b SBCK https://github.com/kanripo/KR1d0026 txt/sbck/KR1d0026
"""

import csv
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Optional

from fastcore.transform import Pipeline

from scripts.lib.documents import KanripoDoc, merge_docs
from scripts.lib.loaders import KanripoTxtDataset
from scripts.lib.transforms import (
    ExtractLayers,
    HealAnnotations,
    KanripoUnicode,
    RemoveChars,
    RemoveComments,
    RemovePageBreaks,
    RemoveWhitespace,
)


def edition_pipeline() -> Pipeline:
    """Cleaning pipeline for source editions, including layer extraction."""
    return Pipeline(
        funcs=[
            KanripoUnicode,
            RemoveComments,
            RemovePageBreaks,
            RemoveChars("0123456789.．¶*"),
            RemoveWhitespace,
            # rejoin small-print groups split at column/page breaks: ")(",
            # and drop intra-group column-break marks: "/"
            HealAnnotations,
            ExtractLayers,
        ]
    )


def load_juan_map(juan_file: Path = Path("assets/juan.csv")) -> dict[str, str]:
    """
    Map each JDSW sub-juan id to the SBCK edition juan it comments on.

    The 老子 juan is not in juan.csv (Lu's chapters don't map 1:1 onto the
    witness's juan); it maps to the whole work, merged by doc_for().
    """
    mapping = {"KR1g0003_025": "KR5c0073"}
    for row in csv.DictReader(open(juan_file, encoding="utf-8")):
        for jdsw_id in row["jdsw_id"].split(","):
            mapping[jdsw_id] = row["sbck_id"]
    return mapping


def group_annotations(
    entries: Iterable[dict], juan_map: dict[str, str]
) -> dict[str, list[dict]]:
    """
    Group annotation entries by the source juan they comment on, in global
    JDSW order (meta.sequence; see docs/corpus.md on why (juan_id, index)
    interleaves lemma sequences and breaks alignment).

    Note: juan.csv's sbck_id is enumerated per hexagram/chapter, a granularity
    that does not match the physical fascicle .txt files the SBCK editions
    ship; per-juan grouping therefore routes most multi-卷 annotations to a
    juan id that has no file or to the wrong fascicle. Prefer group_by_work,
    which merges a work's fascicles and aligns the whole headword sequence.
    """
    by_juan: dict[str, list[dict]] = defaultdict(list)
    for entry in entries:
        source_id = juan_map.get(entry["meta"]["jdsw_id"])
        if source_id:
            by_juan[source_id].append(entry)
    for group in by_juan.values():
        group.sort(key=lambda e: e["meta"]["sequence"])
    return dict(by_juan)


def group_by_work(
    entries: Iterable[dict], docs_csv: Path = Path("assets/docs.csv")
) -> dict[str, list[dict]]:
    """
    Group annotation entries by the work-level SBCK edition they comment on,
    in global JDSW order (meta.sequence).

    The router is built from the docs.csv jdsw_id column, which holds
    work-level JDSW prefixes (sometimes comma-separated, e.g. 尚書 spans
    KR1g0003_003 and KR1g0003_004; both route to the same work). An
    annotation's jdsw_id belongs to prefix p iff it equals p (the bare 老子
    id KR1g0003_025, which has no sub-juan) or starts with ``p + "_"`` — the
    trailing underscore prevents KR1g0003_002 from swallowing KR1g0003_020.

    Aligning per work (one merged text per work) is monotonic across the whole
    headword sequence and matches the physical fascicle layout, unlike the
    per-juan grouping of group_annotations.
    """
    router: list[tuple[str, str]] = []  # (jdsw prefix, work sbck_id)
    for row in csv.DictReader(open(docs_csv, encoding="utf-8")):
        for prefix in row["jdsw_id"].split(","):
            router.append((prefix.strip(), row["sbck_id"]))

    by_work: dict[str, list[dict]] = defaultdict(list)
    for entry in entries:
        jdsw_id = entry["meta"]["jdsw_id"]
        for prefix, sbck_id in router:
            if jdsw_id == prefix or jdsw_id.startswith(prefix + "_"):
                by_work[sbck_id].append(entry)
                break
    for group in by_work.values():
        group.sort(key=lambda e: e["meta"]["sequence"])
    return dict(by_work)


def doc_for(doc_id: str, docs: dict[str, KanripoDoc]) -> Optional[KanripoDoc]:
    """
    Fetch a juan doc by id, merging all of a work's juan when doc_id is
    work-level (e.g. 老子, where the JDSW's single juan spans the witness).
    merge_docs preserves layer spans (offset per part), so the merged doc
    carries layers for layer-aware reading extraction.
    """
    if doc_id in docs:
        return docs[doc_id]
    parts = sorted(id for id in docs if id.startswith(doc_id))
    if parts:
        return merge_docs(*[docs[id] for id in parts])
    return None


def load_clean_docs(source_path: Path) -> dict[str, KanripoDoc]:
    """All Kanripo txt docs under source_path, cleaned and layer-extracted."""
    pipe = edition_pipeline()
    return {doc.id: doc for doc in map(pipe, KanripoTxtDataset(source_path))}
