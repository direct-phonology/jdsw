from unittest import TestCase

from lib.transforms import ExtractAnnotations


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
