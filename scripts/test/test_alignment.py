import unittest

from scripts.lib.alignment import Alignment
from scripts.lib.documents import KanripoDoc

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
