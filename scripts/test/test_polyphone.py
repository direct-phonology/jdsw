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
from scripts.lib.ruzi import RESOLVED, UNRESOLVED, DefaultReadings, Profile

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
        # no layers passed, so layer is unknown rather than a falsely-asserted "main"
        self.assertEqual(records[0]["layer"], "unknown")

        # duruo record: targets the second 過 occurrence
        self.assertEqual(records[1]["char"], "過")
        self.assertEqual(records[1]["reading"], "kwa")
        self.assertEqual(records[1]["span"], [6, 8])


class TestDefaultReadings(unittest.TestCase):
    # mirrors the real schema: a resolved default, plus an inconclusive (empty) one
    PROFILE = DefaultReadings(
        {
            "過": Profile("kwa", 1.0, True),
            "喪": Profile("", 0.0, False),
        }
    )

    def test_resolved(self):
        self.assertEqual(self.PROFILE.resolve("過"), ("kwa", RESOLVED))

    def test_inconclusive_default_is_unresolved(self):
        """an empty ruzi_default (elimination couldn't single one out) is unresolved"""
        self.assertEqual(self.PROFILE.resolve("喪"), (None, UNRESOLVED))

    def test_absent_char_is_unresolved(self):
        self.assertEqual(self.PROFILE.resolve("戈"), (None, UNRESOLVED))

    def test_absent_file_is_empty(self):
        from pathlib import Path

        empty = DefaultReadings.from_csv(Path("does/not/exist.csv"))
        self.assertEqual(empty.resolve("過"), (None, UNRESOLVED))

    def test_committed_profile_loads_and_resolves(self):
        """guard against schema drift in the committed profile asset: a wrong
        column name would silently resolve nothing"""
        from pathlib import Path

        path = Path("assets/default_reading_profiles.csv")
        if not path.exists():
            self.skipTest("profile asset not present")
        profile = DefaultReadings.from_csv(path)
        resolved = [c for c in profile.table if profile.resolve(c)[0] is not None]
        self.assertGreater(len(resolved), 0)


class TestRuziRecords(unittest.TestCase):
    def test_ruzi_resolves_default_reading(self):
        """如字 on a polyphone yields the profile's default reading"""
        text = "君子過矣"
        entries = [{"text": "如字", "meta": {"headword": "過"}}]
        profile = DefaultReadings.of({"過": "kwa"})
        records = list(
            polyphone_records(entries, text, RC, context=4, default_readings=profile)
        )
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["kind"], "ruzi")
        self.assertEqual(records[0]["char"], "過")
        self.assertEqual(records[0]["reading"], "kwa")
        self.assertEqual(records[0]["validation"], VALIDATED)

    def test_ruzi_skipped_without_profile(self):
        """with no profile, 如字 produces nothing rather than guessing"""
        text = "君子過矣"
        entries = [{"text": "如字", "meta": {"headword": "過"}}]
        self.assertEqual(list(polyphone_records(entries, text, RC, context=4)), [])


class TestScopeExpansion(unittest.TestCase):
    def test_down_propagates_to_later_occurrences(self):
        """下同 propagates a reading to later occurrences of the same char,
        up to the next explicit gloss of it"""
        text = "過甲過乙過丙過"  # 過 at 0,2,4,6
        entries = [{"text": "古臥反下同", "meta": {"headword": "過"}}]
        records = list(polyphone_records(entries, text, RC, context=2))
        kinds = [(r["kind"], r["span"][0]) for r in records]
        # one base (fanqie) at 0, three scope copies at 2,4,6
        self.assertEqual(kinds[0], ("fanqie", 0))
        self.assertEqual(
            sorted(s for k, s in kinds if k == "scope"), [2, 4, 6]
        )
        self.assertTrue(all(r["reading"] == "kwaH" for r in records))

    def test_down_stops_at_next_gloss(self):
        """a later explicit gloss of the same char bounds the propagation"""
        text = "過甲過乙過"  # 過 at 0,2,4
        entries = [
            {"text": "古臥反下同", "meta": {"headword": "過"}},  # base at 0
            {"text": "音戈", "meta": {"headword": "過乙"}},  # re-glosses 過 at 2
        ]
        records = list(polyphone_records(entries, text, RC, context=2))
        scope = [r for r in records if r["kind"] == "scope"]
        # propagation from position 0 stops before the re-gloss at 2: no scope copies
        self.assertEqual(scope, [])

    def test_note_is_commentary_only(self):
        """注同 propagates only to occurrences in the commentary layer"""
        text = "過甲過乙過"  # 過 at 0 (main), 2 (commentary), 4 (commentary)
        layers = [(0, 2, "main"), (2, 5, "commentary")]
        entries = [{"text": "古臥反注同", "meta": {"headword": "過"}}]
        records = list(
            polyphone_records(entries, text, RC, context=2, layers=layers)
        )
        scope_positions = sorted(r["span"][0] for r in records if r["kind"] == "scope")
        self.assertEqual(scope_positions, [2, 4])
        self.assertTrue(all(r["layer"] == "commentary" for r in records if r["kind"] == "scope"))
