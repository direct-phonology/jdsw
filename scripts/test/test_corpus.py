"""
Per-work match-rate floors. A regression that silently degrades alignment —
an edition swap, a broken layer extractor, a sort-order mistake — shows up as
a drop in the fraction of lemmata that find a position. These tests pin a
floor below the observed rate (see docs/corpus.md) so such a drop fails CI
instead of passing unnoticed.
"""

import json
from pathlib import Path
from unittest import TestCase

from fastcore.transform import Pipeline

from scripts.lib.alignment import align_sequence, alternate_graphs
from scripts.lib.corpus import edition_pipeline
from scripts.lib.documents import KanripoDoc
from scripts.lib.loaders import KanripoTxtDataset
from scripts.lib.transforms import (
    ExtractAnnotations,
    HealAnnotations,
    KanripoUnicode,
    RemoveChars,
    RemoveComments,
    RemovePageBreaks,
    RemoveWhitespace,
)

FIXTURES = Path(__file__).parent / "fixtures"
ANNOTATIONS = Path("assets/annotations.jsonl")


def match_rate(lemmas: list[str], text: str, alternates: list[tuple]) -> float:
    matches = align_sequence(lemmas, text, alternates=alternates)
    return sum(m.found for m in matches) / len(matches)


def entries_for(jdsw_id: str) -> list[dict]:
    """Annotation entries for one JDSW sub-juan, in global (sequence) order."""
    entries = [
        e
        for line in ANNOTATIONS.read_text(encoding="utf-8").splitlines()
        if jdsw_id in line
        for e in [json.loads(line)]
        if e["meta"]["jdsw_id"] == jdsw_id
    ]
    entries.sort(key=lambda e: e["meta"]["sequence"])
    return entries


class TestSbckFloors(TestCase):
    """
    Real lemmata (annotations.jsonl) against the SBCK commentary editions that
    replaced the CHANT 儀禮/公羊 texts, with the layer extractor in the path.
    The committed fixtures are juan 1 of each; the floor sits below the ~0.93
    observed there (and the ~0.97 full-chapter figure in corpus.md).
    """

    # (jdsw sub-juan, SBCK fixture juan, floor)
    CASES = [
        ("KR1g0003_010_001", "KR1d0026_001", 0.88),  # 儀禮 士冠禮
        ("KR1g0003_021_001", "KR1e0007_001", 0.88),  # 公羊 隱公
    ]

    def test_floors(self) -> None:
        docs = {
            d.id: d
            for d in map(edition_pipeline(), KanripoTxtDataset(FIXTURES / "sbck"))
        }
        for jdsw_id, doc_id, floor in self.CASES:
            with self.subTest(work=doc_id):
                doc = docs[doc_id]
                entries = entries_for(jdsw_id)
                rate = match_rate(
                    [e["meta"]["headword"] for e in entries],
                    doc.text,
                    [alternate_graphs(e["text"]) for e in entries],
                )
                self.assertGreaterEqual(rate, floor, f"{doc_id} fell to {rate:.3f}")

    def test_gongyang_embedded_jdsw_is_separated(self) -> None:
        """KR1e0007 carries Lu Deming's own 音義 inline as 〇/○ groups; the
        extractor must pull them into jdsw_self, not the aligned text, or the
        JDSW matches itself and inflates the rate"""
        docs = {
            d.id: d
            for d in map(edition_pipeline(), KanripoTxtDataset(FIXTURES / "sbck"))
        }
        gongyang = docs["KR1e0007_001"]
        self.assertGreater(len(gongyang.meta["jdsw_self"]), 100)
        self.assertNotIn("〇", gongyang.text)
        self.assertNotIn("○", gongyang.text)
        # the 儀禮 witness has no such embedding
        self.assertEqual(docs["KR1d0026_001"].meta["jdsw_self"], [])


class TestGoldSelfAlignment(TestCase):
    """
    The manually-glossed 論語/孝經 fixtures pair every headword with its gloss
    in situ, so their headwords must align perfectly against their own base
    text. A regression in candidate enumeration or gap-filling that this
    catches would never reach the noisier real-edition path cleanly.
    """

    FIXTURES = [
        FIXTURES / "lunyu" / "Lunyu_JDSWed.txt",
        FIXTURES / "xiaojing" / "Xiaojing_JDSWed.txt",
    ]

    def _pipeline(self) -> Pipeline:
        return Pipeline(
            funcs=[
                KanripoUnicode,
                RemoveComments,
                RemovePageBreaks,
                RemoveChars("0123456789.．¶*"),
                RemoveWhitespace,
                HealAnnotations,
                ExtractAnnotations,
            ]
        )

    def test_self_alignment_is_total(self) -> None:
        pipe = self._pipeline()
        for path in self.FIXTURES:
            with self.subTest(fixture=path.name):
                doc = pipe(KanripoDoc(id=path.stem, text=path.read_text("utf-8")))
                spans = sorted(doc.meta["annotations"].items())
                lemmas = [doc.text[s:e] for (s, e), _ in spans]
                alternates = [alternate_graphs(a) for _, a in spans]
                self.assertEqual(match_rate(lemmas, doc.text, alternates), 1.0)
