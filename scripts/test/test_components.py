from unittest import TestCase

import spacy

from scripts.lib.components import doc_spans_jdsw

# 徐苦感反本亦作埳京劉作欿險也陷也八純卦象水
# 精領反雜卦云通也彖云養而不窮周書云黃帝穿井世本云化益作井宋衷云化益伯益也堯臣廣雅云井深也鄭云井法也字林作井子挺反周云井以不變更爲義師說井以淸絜爲義震宫五世卦


class TestSpanLabeling(TestCase):
    def setUp(self):
        self.nlp = spacy.blank("zh")

    def test_phon_with_meta(self):
        doc = self.nlp.make_doc("爭鬪之爭下及注有爭皆同")
        spans = [(span.text, span.label_) for span in list(doc_spans_jdsw(doc))]
        self.assertEqual(
            spans,
            [
                ("爭鬪之爭", "PHON"),
                ("下及注有爭皆同", "META"),
            ],
        )

    def test_work_with_graf(self):
        doc = self.nlp.make_doc("尚書作罔克胥匡以生")
        spans = [(span.text, span.label_) for span in list(doc_spans_jdsw(doc))]
        self.assertEqual(
            spans,
            [
                ("尚書", "WORK"),
                ("作罔克胥匡以生", "GRAF"),
            ],
        )

    def test_ent_in_meta(self):
        doc = self.nlp.make_doc("都浪反易内皆同有異者别出")
        spans = [(span.text, span.label_) for span in list(doc_spans_jdsw(doc))]
        self.assertEqual(
            spans,
            [
                ("都浪反", "PHON"),
                ("易", "WORK"),
                ("内皆同", "META"),
                ("有異者别出", ""),
            ],
        )

    def test_multi_graf(self):
        doc = self.nlp.make_doc("本又作縻同亡池反散也干同徐又武寄反又亡彼反韓詩云共也孟同埤蒼作縻云散也陸作䌕京作劘")
        spans = [(span.text, span.label_) for span in list(doc_spans_jdsw(doc))]
        self.assertEqual(
            spans,
            [
                ("本", "WORK"),
                ("又作縻", "GRAF"),
                ("同亡池反", "PHON"),
                ("散也", "SEM"),
                ("干", "PER"),
                ("同", "MARKER"),
                ("徐", "PER"),
                ("又武寄反", "PHON"),
                ("又亡彼反", "PHON"),
                ("韓詩", "WORK"),
                ("云", "MARKER"),
                ("共也", "SEM"),
                ("孟", "PER"),
                ("同", "MARKER"),
                ("埤蒼", "WORK"),
                ("作縻", "GRAF"),
                ("云", "MARKER"),
                ("散也", "SEM"),
                ("陸", "PER"),
                ("作䌕", "GRAF"),
                ("京", "PER"),
                ("作劘", "GRAF"),
            ],
        )

    def test_multi_source(self):
        doc = self.nlp.make_doc("音橘徐又居密反鄭云綆也方言云關西謂綆爲繘郭璞云汲水索也又其律反又音述")
        spans = [(span.text, span.label_) for span in list(doc_spans_jdsw(doc))]
        self.assertEqual(
            spans,
            [
                ("音橘", "PHON"),
                ("徐", "PER"),
                ("又居密反", "PHON"),
                ("鄭", "PER"),
                ("云", "MARKER"),
                ("綆也", "SEM"),
                ("方言", "WORK"),
                ("云", "MARKER"),
                ("關西謂綆爲繘", ""),
                ("郭璞", "PER"),
                ("云", "MARKER"),
                ("汲水索也", "SEM"),
                ("又其律反", "PHON"),
                ("又音述", "PHON"),
            ],
        )

    def test_multi_sem(self):
        doc = self.nlp.make_doc("節計反下卦同鄭云旣巳也盡也濟度也坎宫三世卦")
        spans = [(span.text, span.label_) for span in list(doc_spans_jdsw(doc))]
        self.assertEqual(
            spans,
            [
                ("節計反", "PHON"),
                ("下卦同", "META"),
                ("鄭", "PER"),
                ("云", "MARKER"),
                ("旣巳也", "SEM"),
                ("盡也", "SEM"),
                ("濟度也", "SEM"),
                ("坎宫三世卦", "WORK"),
            ],
        )

    def test_repeated_sources(self):
        doc = self.nlp.make_doc("本亦作壺京馬鄭王肅翟子玄作壺")
        spans = [(span.text, span.label_) for span in list(doc_spans_jdsw(doc))]
        self.assertEqual(
            spans,
            [
                ("本", "WORK"),
                ("亦作壺", "GRAF"),
                ("京", "PER"),
                ("馬", "PER"),
                ("鄭", "PER"),
                ("王肅", "PER"),
                ("翟子玄", "PER"),
                ("作壺", "GRAF"),
            ],
        )
