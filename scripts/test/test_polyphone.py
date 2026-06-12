import unittest

import pandas as pd

from scripts.lib.phonology import Reconstruction
from scripts.lib.polyphone import (
    AMBIGUOUS,
    UNVALIDATED,
    VALIDATED,
    extract_readings,
    locate_targets,
    polyphone_records,
)

# minimal Guangyun-style table: 過 is a polyphone (kwaH / kwa)
TABLE = pd.DataFrame(
    [
        {"char": "古", "initial": "k", "rime": "uX", "reading": "kuX"},
        {"char": "臥", "initial": "ng", "rime": "waH", "reading": "ngwaH"},
        {"char": "過", "initial": "k", "rime": "waH", "reading": "kwaH"},
        {"char": "過", "initial": "k", "rime": "wa", "reading": "kwa"},
        {"char": "戈", "initial": "k", "rime": "wa", "reading": "kwa"},
        {"char": "不", "initial": "p", "rime": "juw", "reading": "pjuw"},
    ]
)
RC = Reconstruction(TABLE)


class TestExtractReadings(unittest.TestCase):
    def test_fanqie(self):
        readings = extract_readings("古臥反", RC)
        self.assertEqual(len(readings), 1)
        self.assertEqual(readings[0].kind, "fanqie")
        self.assertEqual(readings[0].mc, "kwaH")

    def test_duruo(self):
        readings = extract_readings("音戈", RC)
        self.assertEqual(len(readings), 1)
        self.assertEqual(readings[0].kind, "duruo")
        self.assertEqual(readings[0].mc, "kwa")

    def test_duruo_inside_fanqie_not_doubled(self):
        """音XY反 is one fanqie reading, not a fanqie plus a duruo"""
        readings = extract_readings("音古臥反", RC)
        self.assertEqual([r.kind for r in readings], ["fanqie"])

    def test_multiple_readings(self):
        readings = extract_readings("古臥反又音戈", RC)
        self.assertEqual([r.kind for r in readings], ["fanqie", "duruo"])

    def test_unknown_chars_yield_no_mc(self):
        readings = extract_readings("丑亮反", RC)
        self.assertEqual(len(readings), 1)
        self.assertIsNone(readings[0].mc)


class TestLocateTargets(unittest.TestCase):
    def test_validated(self):
        offsets, validation = locate_targets("不過", "kwaH", RC)
        self.assertEqual((offsets, validation), ([1], VALIDATED))

    def test_ambiguous(self):
        offsets, validation = locate_targets("戈過", "kwa", RC)
        self.assertEqual((offsets, validation), ([0, 1], AMBIGUOUS))

    def test_unvalidated(self):
        offsets, validation = locate_targets("不古", "kwaH", RC)
        self.assertEqual((offsets, validation), ([], UNVALIDATED))


class TestPolyphoneRecords(unittest.TestCase):
    def test_records(self):
        text = "君子不過矣戈過之"
        entries = [
            {"text": "古臥反", "meta": {"headword": "不過", "index": 1}},
            {"text": "音戈", "meta": {"headword": "過之", "index": 2}},
        ]
        records = list(polyphone_records(entries, text, RC, context=4))

        # fanqie record: 過 at position 3 validates uniquely
        self.assertEqual(records[0]["char"], "過")
        self.assertEqual(records[0]["reading"], "kwaH")
        self.assertEqual(records[0]["validation"], VALIDATED)
        offset = records[0]["offset"]
        self.assertEqual(records[0]["text"][offset], "過")
        self.assertEqual(records[0]["layer"], "main")

        # duruo record: targets the second 過 occurrence
        self.assertEqual(records[1]["char"], "過")
        self.assertEqual(records[1]["reading"], "kwa")
        self.assertEqual(records[1]["span"], [6, 8])
