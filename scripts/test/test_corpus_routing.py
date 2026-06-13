"""
group_by_work routes every annotation to its work-level SBCK edition using the
docs.csv jdsw_id prefixes. The cases that broke per-juan grouping must hold:
the bare 老子 id (no sub-juan), comma-listed prefixes routing to one work, and
the trailing-underscore guard that keeps KR1g0003_002 from swallowing
KR1g0003_020. And no annotation may be dropped.
"""

from pathlib import Path
from unittest import TestCase

import srsly

from scripts.lib.corpus import group_by_work

ANNOTATIONS = Path("assets/annotations.jsonl")
DOCS = Path("assets/docs.csv")


def entry(jdsw_id: str, sequence: int = 0) -> dict:
    return {"meta": {"jdsw_id": jdsw_id, "sequence": sequence, "headword": "x"}}


class TestGroupByWork(TestCase):
    def test_laozi_bare_id_routes_by_exact_match(self) -> None:
        groups = group_by_work([entry("KR1g0003_025")], DOCS)
        self.assertEqual(list(groups), ["KR5c0073"])

    def test_comma_listed_prefixes_route_to_one_work(self) -> None:
        # 尚書 = KR1g0003_003,KR1g0003_004 -> both -> KR1b0002
        groups = group_by_work(
            [entry("KR1g0003_003_001"), entry("KR1g0003_004_007")], DOCS
        )
        self.assertEqual(list(groups), ["KR1b0002"])
        self.assertEqual(len(groups["KR1b0002"]), 2)

    def test_002_does_not_collide_with_020(self) -> None:
        # 周易 KR1g0003_002 -> KR1a0006; 左傳 KR1g0003_020 -> KR1e0002
        groups = group_by_work(
            [entry("KR1g0003_002_001"), entry("KR1g0003_020_001")], DOCS
        )
        self.assertEqual(groups["KR1a0006"][0]["meta"]["jdsw_id"], "KR1g0003_002_001")
        self.assertEqual(groups["KR1e0002"][0]["meta"]["jdsw_id"], "KR1g0003_020_001")

    def test_groups_sorted_by_sequence(self) -> None:
        groups = group_by_work(
            [entry("KR1g0003_002_002", 5), entry("KR1g0003_002_001", 2)], DOCS
        )
        seqs = [e["meta"]["sequence"] for e in groups["KR1a0006"]]
        self.assertEqual(seqs, [2, 5])

    def test_every_annotation_routes(self) -> None:
        entries = list(srsly.read_jsonl(ANNOTATIONS))
        groups = group_by_work(entries, DOCS)
        routed = sum(len(g) for g in groups.values())
        self.assertEqual(routed, len(entries))
