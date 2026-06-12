import json
import unittest
from pathlib import Path

from scripts.lib.variants import NORMALIZATION_PATH, VARIANTS_PATH, normalize


class TestVariantTable(unittest.TestCase):
    def test_tables_are_disjoint_layers(self):
        """normalization and variant tables must not disagree on any key"""
        normalization = json.loads(NORMALIZATION_PATH.read_text(encoding="utf-8"))
        variants = json.loads(VARIANTS_PATH.read_text(encoding="utf-8"))
        overlap = set(normalization) & set(variants)
        self.assertEqual(overlap, set())

    def test_normalize_applies_both_layers(self):
        # mechanical: fullwidth punctuation folds to ascii
        self.assertEqual(normalize("："), ":")
        # philological: curated variant pairs
        self.assertEqual(normalize("别"), "別")
        self.assertEqual(normalize("㐀"), "丘")

    def test_normalize_preserves_length(self):
        """every mapping is 1:1, so offsets survive normalization"""
        text = "本又作：别㐀"
        self.assertEqual(len(normalize(text)), len(text))
