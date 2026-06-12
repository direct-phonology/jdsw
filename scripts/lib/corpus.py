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
    """
    by_juan: dict[str, list[dict]] = defaultdict(list)
    for entry in entries:
        source_id = juan_map.get(entry["meta"]["jdsw_id"])
        if source_id:
            by_juan[source_id].append(entry)
    for group in by_juan.values():
        group.sort(key=lambda e: e["meta"]["sequence"])
    return dict(by_juan)


def doc_for(doc_id: str, docs: dict[str, KanripoDoc]) -> Optional[KanripoDoc]:
    """
    Fetch a juan doc by id, merging all of a work's juan when doc_id is
    work-level (e.g. 老子, where the JDSW's single juan spans the witness).
    Layer spans don't survive merging; merged docs carry no layers.
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
