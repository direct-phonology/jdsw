import unittest

from scripts.lib.alignment import (
    ALTERNATE,
    ANCHOR,
    GAP,
    PARTIAL,
    UNMATCHED,
    Alignment,
    align_sequence,
    alternate_graphs,
)
from scripts.lib.documents import KanripoDoc


class TestAlignSequence(unittest.TestCase):
    def test_common_char_does_not_derail(self):
        """a common character matching a wrong early instance must not derail
        the alignment of later multi-character lemmas (the greedy failure mode)"""
        # true position of 也 is after the anchor, but it also occurs at 0
        text = "也大學之道在止於至善也"
        matches = align_sequence(["大學之道", "也"], text)
        self.assertEqual((matches[0].start, matches[0].end), (1, 5))
        self.assertEqual(matches[0].confidence, ANCHOR)
        self.assertEqual((matches[1].start, matches[1].end), (10, 11))

    def test_monotonic(self):
        """matched positions must be strictly increasing in lemma order"""
        text = "寡人之於國也盡心焉耳矣河內凶則移其民於河東移其粟於河內"
        matches = align_sequence(["寡人", "河內", "河東", "河內"], text)
        positions = [m.start for m in matches if m.found]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual((matches[1].start, matches[3].start), (11, 25))

    def test_repeated_lemma_prefers_earlier_on_tie(self):
        """deterministic: equal-weight alternatives resolve to earlier positions"""
        matches = align_sequence(["寡人"], "或謂寡人勿取或謂寡人取之")
        self.assertEqual((matches[0].start, matches[0].end), (2, 4))

    def test_gap_fill_between_anchors(self):
        """lemmas without an anchor are placed in the window between anchors"""
        text = "甲乙丙丁戊己庚辛壬癸"
        matches = align_sequence(["甲乙丙", "戊", "庚辛壬"], text)
        self.assertEqual(matches[1].confidence, ANCHOR)  # unique, so anchored
        # a char occurring only in the gap window still lands correctly
        matches = align_sequence(["甲乙丙", "丁", "庚辛壬"], text)
        self.assertEqual((matches[1].start, matches[1].end), (3, 4))

    def test_unmatched_lemma_is_reported(self):
        """a lemma absent from the text is flagged, not silently misplaced"""
        matches = align_sequence(["甲乙丙", "魚魚", "庚辛壬"], "甲乙丙丁戊己庚辛壬癸")
        self.assertEqual(matches[1].confidence, UNMATCHED)
        self.assertIsNone(matches[1].start)
        # neighbors are unaffected
        self.assertEqual(matches[0].confidence, ANCHOR)
        self.assertEqual(matches[2].confidence, ANCHOR)

    def test_partial_match(self):
        """a lemma whose graph differs from the base text matches by prefix"""
        matches = align_sequence(["甲乙丙", "戊新", "庚辛壬"], "甲乙丙丁戊己庚辛壬癸")
        self.assertEqual(matches[1].confidence, PARTIAL)
        self.assertEqual((matches[1].start, matches[1].end), (4, 6))

    def test_partial_requires_two_verified_chars(self):
        """a lemma of 3+ characters must verify at least 2 to match partially;
        a single common character is not evidence of position"""
        matches = align_sequence(["甲乙丙"], "甲丁戊")
        self.assertEqual(matches[0].confidence, UNMATCHED)
        # 2-character lemmas may still match on a single character
        matches = align_sequence(["甲乙"], "甲丁")
        self.assertEqual(matches[0].confidence, PARTIAL)

    def test_partial_tail_does_not_consume_next_lemma(self):
        """the unverified tail of a partial must not advance the gap-fill
        cursor past the next lemma's true position"""
        matches = align_sequence(["甲乙子", "丙丁"], "甲乙丙戊")
        self.assertEqual(matches[0].confidence, PARTIAL)
        self.assertEqual(matches[0].verified_end, 2)  # only 甲乙 verified
        # 丙 sits inside the first partial's extrapolated tail; it must
        # still be reachable
        self.assertEqual(matches[1].confidence, PARTIAL)
        self.assertEqual(matches[1].start, 2)

    def test_damaged_char_is_wildcard(self):
        """a ⬤ placeholder in the text matches any lemma character exactly,
        instead of being absorbed by a lossy prefix match"""
        matches = align_sequence(["甲乙丙", "戊己", "庚辛壬"], "甲乙丙丁⬤己庚辛壬癸")
        self.assertEqual(matches[1].confidence, GAP)
        self.assertEqual((matches[1].start, matches[1].end), (4, 6))
        # single-char lemma over a damaged char
        matches = align_sequence(["甲乙丙", "戊", "庚辛壬"], "甲乙丙丁⬤己庚辛壬癸")
        self.assertEqual((matches[1].start, matches[1].end), (4, 5))

    def test_alternate_graph_recovery(self):
        """a lemma absent from the text is recovered via the alternative
        graph its own gloss cites (本又作X)"""
        text = "甲乙丙丁戊己庚辛壬癸"
        lemmas = ["甲乙丙", "戊新", "庚辛壬"]
        alternates = [(), ("己",), ()]
        matches = align_sequence(lemmas, text, alternates=alternates)
        self.assertEqual(matches[1].confidence, ALTERNATE)
        self.assertEqual((matches[1].start, matches[1].end), (4, 6))


class TestAlternateGraphs(unittest.TestCase):
    def test_formulae(self):
        self.assertEqual(alternate_graphs("本又作措又作厝同七路反"), ("措", "厝"))
        self.assertEqual(alternate_graphs("本亦作己"), ("己",))
        self.assertEqual(alternate_graphs("一本作虛"), ("虛",))

    def test_other_texts_graphs_are_not_alternates(self):
        """citations of other texts' graphs (說文作X) are not 本-variants"""
        self.assertEqual(alternate_graphs("說文作䞓又作赬"), ())
        self.assertEqual(alternate_graphs("音洛"), ())


class TestAlignmentReport(unittest.TestCase):
    def test_confidence_and_layer(self):
        """the alignment report records confidence and edition layer per lemma"""
        x = KanripoDoc(
            id="x",
            text="甲乙丙丁戊己庚辛壬癸",
            meta={"layers": [(0, 5, "main"), (5, 10, "commentary")]},
        )
        y = KanripoDoc(
            id="y",
            text="乙丙庚辛",
            meta={"annotations": {(0, 2): "one", (2, 4): "two"}},
        )
        report = Alignment(x, y).align_annotations().x.meta["alignment"]
        self.assertEqual(report[0]["confidence"], ANCHOR)
        self.assertEqual(report[0]["layer"], "main")
        self.assertEqual(report[1]["x_span"], (6, 8))
        self.assertEqual(report[1]["layer"], "commentary")

class TestAlignAnnotations(unittest.TestCase):
    def test_headgraphs(self):
        """should align headwords consisting of a single character"""
        x = KanripoDoc(id="x", text="abcdefghi")
        y = KanripoDoc(
            id="y",
            text="abf",
            meta={
                "annotations": {
                    (0, 1): "one",
                    (1, 2): "two",
                    (2, 3): "three",
                }
            },
        )
        alignment = Alignment(x, y)
        alignment.align_annotations()
        self.assertEqual(
            x.meta["annotations"],
            {
                (0, 1): "one",
                (1, 2): "two",
                (5, 6): "three",
            },
        )

    def test_headwords(self):
        """should align headwords consisting of multiple characters"""
        x = KanripoDoc(id="x", text="abcdefghi")
        y = KanripoDoc(
            id="y",
            text="bcefg",
            meta={
                "annotations": {
                    (0, 2): "one",
                    (2, 5): "two",
                }
            },
        )
        alignment = Alignment(x, y)
        alignment.align_annotations()
        self.assertEqual(
            x.meta["annotations"],
            {
                (1, 3): "one",
                (4, 7): "two",
            },
        )

    def test_fuzzy_match(self):
        """should align headwords that differ slightly from base text"""
        x = KanripoDoc(
            id="KR5c0126_024",
            text="徐无鬼第二十四徐无鬼因女商見魏武侯，武侯勞之曰：「先生病矣！苦於山林之勞，故乃肯見於寡人。」徐无鬼曰：「我則勞於君，君有何勞於我！君將盈嗜欲，長好惡，",
        )
        y = KanripoDoc(
            id="KR1g0003_028_002",
            text="徐无鬼第二十四徐无鬼女商魏武侯武侯勞之盈耆長",
            meta={
                "annotations": {
                    (0, 7): "以人名篇",
                    (7, 10): "緡山人魏之隱士也司馬本作緡山人徐无鬼",
                    (10, 12): "人名也李云无鬼女商並魏幸臣",
                    (12, 15): "名擊文侯之子治安邑",
                    (15, 19): "力報反唯山林之勞一字如字餘并下章並力報反",
                    (19, 21): "時志反下注同",   # 盈耆
                    (21, 22): "丁丈反",
                }
            },
        )
        alignment = Alignment(x, y)
        alignment.align_annotations()
        self.assertEqual(
            x.meta["annotations"],
            {
                (0, 7): "以人名篇",
                (7, 10): "緡山人魏之隱士也司馬本作緡山人徐无鬼",
                (11, 13): "人名也李云无鬼女商並魏幸臣",
                (14, 17): "名擊文侯之子治安邑",
                (18, 22): "力報反唯山林之勞一字如字餘并下章並力報反",
                (67, 69): "時志反下注同",   # 盈嗜; second graph differs from y
                (71, 72): "丁丈反",
            },
        )
