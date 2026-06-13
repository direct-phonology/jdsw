from unittest import TestCase

from scripts.lib.transforms import ExtractAnnotations, ExtractLayers


class TestExtractAnnotations(TestCase):
    def test_single_char_headwords(self):
        """should handle headwords consisting of a single character"""
        text, annotations = ExtractAnnotations().encodes("a(b)c(d)e(f)g(h)")
        self.assertEqual(text, "aceg")
        self.assertEqual(
            annotations,
            {
                (0, 1): "b",
                (1, 2): "d",
                (2, 3): "f",
                (3, 4): "h",
            },
        )

    def test_multi_char_headwords(self):
        """should handle headwords consisting of multiple characters"""
        text, annotations = ExtractAnnotations().encodes("a(bcde)f(gh)")
        self.assertEqual(text, "af")
        self.assertEqual(
            annotations,
            {
                (0, 1): "bcde",
                (1, 2): "gh",
            },
        )

    def test_discard_extra_annotations(self):
        """annotations that don't have a headword should be discarded"""
        text, annotations = ExtractAnnotations().encodes("efgh(ijkl)(abcd)")
        self.assertEqual(text, "efgh")
        self.assertEqual(annotations, {(0, 4): "ijkl"})

    def test_discard_extra_headwords(self):
        """headwords that don't have an annotation should be discarded"""
        text, annotations = ExtractAnnotations().encodes("abcd(efgh)ijkl")
        self.assertEqual(text, "abcd")
        self.assertEqual(annotations, {(0, 4): "efgh"})


class TestExtractLayers(TestCase):
    def test_main_and_commentary(self):
        """parenthesized commentary is kept but labeled, parens dropped"""
        text, layers, jdsw_self = ExtractLayers().extract("甲乙(丙丁)戊")
        self.assertEqual(text, "甲乙丙丁戊")
        self.assertEqual(
            layers, [(0, 2, "main"), (2, 4, "commentary"), (4, 5, "main")]
        )
        self.assertEqual(jdsw_self, [])

    def test_jdsw_self_spans_are_removed(self):
        """〇-initial groups are the JDSW's own embedded 音義: removed from
        the cleaned text (so the JDSW can't align against itself) and
        recorded with their insertion position"""
        text, layers, jdsw_self = ExtractLayers().extract("甲(〇陸曰佳買反)乙(注也)")
        self.assertEqual(text, "甲乙注也")
        self.assertEqual(layers, [(0, 2, "main"), (2, 4, "commentary")])
        self.assertEqual(jdsw_self, [(1, "〇陸曰佳買反")])

    def test_jdsw_self_mid_group(self):
        """a group can carry the commentary and the 音義 together
        (注〇音義); everything from the marker to the group's end is the
        JDSW's, what precedes it is the commentator's"""
        text, layers, jdsw_self = ExtractLayers().extract("甲(注也〇陸曰反)乙")
        self.assertEqual(text, "甲注也乙")
        self.assertEqual(
            layers, [(0, 1, "main"), (1, 3, "commentary"), (3, 4, "main")]
        )
        self.assertEqual(jdsw_self, [(3, "〇陸曰反")])

    def test_nested_and_unterminated_groups(self):
        """nested parens fold into the enclosing group; an unterminated
        group at end of text is still flushed"""
        text, layers, _ = ExtractLayers().extract("甲(乙(丙)丁)戊(己")
        self.assertEqual(text, "甲乙丙丁戊己")
        self.assertEqual(
            layers,
            [(0, 1, "main"), (1, 4, "commentary"), (4, 5, "main"), (5, 6, "commentary")],
        )

    def test_fullwidth_parens(self):
        """fullwidth parens mark commentary the same as ASCII ones"""
        text, layers, _ = ExtractLayers().extract("甲（乙）")
        self.assertEqual(text, "甲乙")
        self.assertEqual(layers, [(0, 1, "main"), (1, 2, "commentary")])

    def test_yinyiyue_marker(self):
        """音義曰 inside a group opens Lu's embedded 音義 (SBCK 莊子), where the
        篇-initial block uses the phrase rather than a circle"""
        text, layers, jdsw_self = ExtractLayers().extract("甲(注也音義曰逍如字)乙")
        self.assertEqual(text, "甲注也乙")
        self.assertEqual(
            layers, [(0, 1, "main"), (1, 3, "commentary"), (3, 4, "main")]
        )
        self.assertEqual(jdsw_self, [(3, "音義曰逍如字")])

    def test_no_markup_is_unknown(self):
        """a witness with no paren markup (ZTDZ 老子: 經 and 注 full-size and
        undelimited) yields no layer signal, so it is labeled unknown rather
        than a falsely-confident main"""
        text, layers, jdsw_self = ExtractLayers().extract("道可道非常道")
        self.assertEqual(text, "道可道非常道")
        self.assertEqual(layers, [(0, 6, "unknown")])
        self.assertEqual(jdsw_self, [])
