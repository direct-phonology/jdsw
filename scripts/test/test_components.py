from unittest import TestCase

import spacy
from scripts.recipes.spancat import doc_spans_jdsw
import debugpy

# 徐苦感反本亦作埳京劉作欿險也陷也八純卦象水
# 精領反雜卦云通也彖云養而不窮周書云黃帝穿井世本云化益作井宋衷云化益伯益也堯臣廣雅云井深也鄭云井法也字林作井子挺反周云井以不變更爲義師說井以淸絜爲義震宫五世卦


class TestSplitOnStr(TestCase):
    def setUp(self):
        self.nlp = spacy.blank("zh")

    def test_phon_with_meta(self):
        doc = self.nlp.make_doc("爭鬪之爭下及注有爭皆同")
        spans = [(span.text, span.label_) for span in list(doc_spans_jdsw(doc))]
        self.assertEqual(
            spans,
            [
                ("爭鬪之爭", "PHONETIC"),
                ("下及注有爭皆同", "META"),
            ],
        )

    def test_graphic(self):
        doc = self.nlp.make_doc("尚書作罔克胥匡以生")
        spans = [(span.text, span.label_) for span in list(doc_spans_jdsw(doc))]
        self.assertEqual(
            spans,
            [
                ("尚書", "WORK_OF_ART"),
                ("作罔克胥匡以生", "GRAPHIC"),
            ],
        )

    def test_multi_graphic(self):
        doc = self.nlp.make_doc("本又作縻同亡池反散也干同徐又武寄反又亡彼反韓詩云共也孟同埤蒼作縻云散也陸作䌕京作劘")
        spans = [(span.text, span.label_) for span in list(doc_spans_jdsw(doc))]
        self.assertEqual(
            spans,
            [
                ("本", "WORK_OF_ART"),
                ("又作縻", "GRAPHIC"),
                ("同亡池反", "PHONETIC"),
                ("散也", "SEMANTIC"),
                ("干", "PERSON"),
                ("同", "MARKER"),
                ("徐", "PERSON"),
                ("又武寄反", "PHONETIC"),
                ("又亡彼反", "PHONETIC"),
                ("韓詩", "WORK_OF_ART"),
                ("云", "MARKER"),
                ("共也", "SEMANTIC"),
                ("孟", "PERSON"),
                ("同", "MARKER"),
                ("埤蒼", "WORK_OF_ART"),
                ("作縻", "GRAPHIC"),
                ("云", "MARKER"),
                ("散也", "SEMANTIC"),
                ("陸", "PERSON"),
                ("作䌕", "GRAPHIC"),
                ("京", "PERSON"),
                ("作劘", "GRAPHIC"),
            ],
        )

    def test_multi_source(self):
        doc = self.nlp.make_doc("音橘徐又居密反鄭云綆也方言云關西謂綆爲繘郭璞云汲水索也又其律反又音述")
        spans = [(span.text, span.label_) for span in list(doc_spans_jdsw(doc))]
        self.assertEqual(
            spans,
            [
                ("音橘", "PHONETIC"),
                ("徐", "PERSON"),
                ("又居密反", "PHONETIC"),
                ("鄭", "PERSON"),
                ("云", "MARKER"),
                ("綆也", "SEMANTIC"),
                ("方言", "WORK_OF_ART"),
                ("云", "MARKER"),
                ("關西謂綆爲繘", ""),
                ("郭璞", "PERSON"),
                ("云", "MARKER"),
                ("汲水索也", "SEMANTIC"),
                ("又其律反", "PHONETIC"),
                ("又音述", "PHONETIC"),
            ],
        )

    def test_multi_semantic(self):
        doc = self.nlp.make_doc("節計反下卦同鄭云旣巳也盡也濟度也坎宫三世卦")
        debugpy.breakpoint()
        spans = [(span.text, span.label_) for span in list(doc_spans_jdsw(doc))]
        self.assertEqual(
            spans,
            [
                ("節計反", "PHONETIC"),
                ("下卦同", "META"),
                ("鄭", "PERSON"),
                ("云", "MARKER"),
                ("旣巳也", "SEMANTIC"),
                ("盡也", "SEMANTIC"),
                ("濟度也", "SEMANTIC"),
                ("坎宫三世卦", "WORK_OF_ART"),
            ]
        )
