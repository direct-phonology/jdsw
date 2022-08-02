from unittest import TestCase

import pandas as pd

from lib.phonology import Reconstruction
from lib.util import align_refs, split_sentences


class TestAlignRefs(TestCase):
    def test_realign(self) -> None:
        rc = Reconstruction(
            pd.DataFrame.from_dict(
                {
                    "char": ["去"],
                    "reading": ["khjoX"],
                    "initial": ["kh"],
                    "rime": ["joX"],
                }
            )
        )
        text = "去\t_\n不\tkhjoX\n大\t_"
        self.assertEqual(align_refs(text, rc), "去\tkhjoX\n不\t_\n大\t_")

    def test_extended_realign(self) -> None:
        pass

    def test_no_realign(self) -> None:
        pass

    def test_no_match_guangyun(self) -> None:
        pass

    def test_edges(self) -> None:
        pass


class TestSplitSentences(TestCase):
    def test_no_split(self) -> None:
        text = "仲子生而有文在其手，曰為魯夫人，故仲子歸于我。"
        self.assertEqual(split_sentences(text), [text])

    def test_split(self) -> None:
        text = "北冥有魚，其名為鯤。鯤之大，不知其幾千里也。化而為鳥，其名為鵬。"
        self.assertEqual(
            split_sentences(text),
            [
                "北冥有魚，其名為鯤。",
                "鯤之大，不知其幾千里也。",
                "化而為鳥，其名為鵬。",
            ],
        )

    def test_quote(self) -> None:
        text = "子曰：「上下无常，非為邪也。進退无恆，非離群也。君子進德脩業、欲及時也，故无咎。」"
        self.assertEqual(
            split_sentences(text),
            [
                "子曰：「上下无常，非為邪也。",
                "進退无恆，非離群也。",
                "君子進德脩業、欲及時也，故无咎。」",
            ],
        )

    def test_multi_quote(self) -> None:
        text = "子曰：「然。」「然則何如？」"
        self.assertEqual(
            split_sentences(text),
            [
                "子曰：「然。」「",
                "然則何如？」",
            ],
        )
