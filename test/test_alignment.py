import unittest

from lib.alignment import Alignment
from lib.documents import KanripoDoc

ZHUANGZI_INPUT_JDSW = KanripoDoc(
    id="KR1g0003_028_002",
    text="徐无鬼第二十四徐无鬼女商魏武侯武侯勞之盈耆長",
    meta={
        "annotations": {
            6: "以人名篇",
            9: "緡山人魏之隱士也司馬本作緡山人徐无鬼",
            11: "人名也李云无鬼女商並魏幸臣",
            14: "名擊文侯之子治安邑",
            18: "力報反唯山林之勞一字如字餘并下章並力報反",
            20: "時志反下注同",
            21: "丁丈反",
        }
    },
)

ZHUANGZI_INPUT_ZHENGWEN = KanripoDoc(
    id="KR5c0126_024",
    text="徐无鬼第二十四徐无鬼因女商見魏武侯，武侯勞之曰：「先生病矣！苦於山林之勞，故乃肯見於寡人。」徐无鬼曰：「我則勞於君，君有何勞於我！君將盈嗜欲，長好惡，",
)

ZHUANGZI_OUTPUT = KanripoDoc(
    id="KR5c0126_024",
    text="徐无鬼第二十四徐无鬼因女商見魏武侯，武侯勞之曰：「先生病矣！苦於山林之勞，故乃肯見於寡人。」徐无鬼曰：「我則勞於君，君有何勞於我！君將盈嗜欲，長好惡，",
    meta={
        "annotations": {
            6: "以人名篇",
            9: "緡山人魏之隱士也司馬本作緡山人徐无鬼",
            12: "人名也李云无鬼女商並魏幸臣",
            16: "名擊文侯之子治安邑",
            21: "力報反唯山林之勞一字如字餘并下章並力報反",
            68: "時志反下注同",
            71: "丁丈反",
        }
    },
)


class TestAlignment(unittest.TestCase):
    def test_align_annotations(self):
        alignment = Alignment(ZHUANGZI_INPUT_ZHENGWEN, ZHUANGZI_INPUT_JDSW)
        alignment.align_annotations()
        self.assertEqual(
            list(alignment.x.meta["annotations"].items()),
            list(ZHUANGZI_OUTPUT.meta["annotations"].items()),
        )
