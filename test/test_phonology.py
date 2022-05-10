from unittest import TestCase

import pandas as pd

from lib.phonology import Reconstruction, NoReadingError, MultipleReadingsError


class TestReconstruction(TestCase):
    def test_init(self):
        """dedupes input table on init"""
        rc = Reconstruction(
            pd.DataFrame.from_dict(
                {
                    "zi": ["東", "東"],
                    "MC": ["tuwng", "tuwng"],
                    "MCInitial": ["t-", "t-"],
                    "MCfinal": ["-uwng", "-uwng"],
                }
            )
        )
        self.assertEqual(rc.table.shape[0], 1)

    def test_reading_for(self):
        """returns a reading for a given character"""
        rc = Reconstruction(
            pd.DataFrame.from_dict(
                {
                    "zi": ["東"],
                    "MC": ["tuwng"],
                    "MCInitial": ["t-"],
                    "MCfinal": ["-uwng"],
                }
            )
        )
        self.assertEqual(rc.reading_for("東"), "tuwng")

    def test_readings_for(self):
        """returns all readings for a given character"""
        rc = Reconstruction(
            pd.DataFrame.from_dict(
                {
                    "zi": ["不", "不"],
                    "MC": ["pjut", "pjuw"],
                    "MCInitial": ["p-", "p-"],
                    "MCfinal": ["-jut", "-juw"],
                }
            )
        )
        self.assertEqual(rc.readings_for("不"), ["pjut", "pjuw"])

    def test_is_valid_reading(self):
        """returns True if a given reading is valid for a given character"""
        rc = Reconstruction(
            pd.DataFrame.from_dict(
                {
                    "zi": ["東"],
                    "MC": ["tuwng"],
                    "MCInitial": ["t-"],
                    "MCfinal": ["-uwng"],
                }
            )
        )
        self.assertTrue(rc.is_valid_reading("東", "tuwng"))
        self.assertFalse(rc.is_valid_reading("東", "pjut"))

    def test_reading_for_missing_char(self):
        """errors if no reading for a given character"""
        rc = Reconstruction(
            pd.DataFrame.from_dict(
                {
                    "zi": ["東"],
                    "MC": ["tuwng"],
                    "MCInitial": ["t-"],
                    "MCfinal": ["-uwng"],
                }
            )
        )
        with self.assertRaises(NoReadingError):
            rc.reading_for("西")

    def test_reading_for_polyphone(self):
        """errors if multiple readings for a given character"""
        rc = Reconstruction(
            pd.DataFrame.from_dict(
                {
                    "zi": ["不", "不"],
                    "MC": ["pjut", "pjuw"],
                    "MCInitial": ["p-", "p-"],
                    "MCfinal": ["-jut", "-juw"],
                }
            )
        )
        with self.assertRaises(MultipleReadingsError):
            rc.reading_for("不")

    def test_initial_for(self):
        """returns the initial for a given character"""
        rc = Reconstruction(
            pd.DataFrame.from_dict(
                {
                    "zi": ["東"],
                    "MC": ["tuwng"],
                    "MCInitial": ["t-"],
                    "MCfinal": ["-uwng"],
                }
            )
        )
        self.assertEqual(rc.initial_for("東"), "t-")

    def test_initial_for_rhmying_polyphone(self):
        """returns the initial for a character with multiple finals"""
        rc = Reconstruction(
            pd.DataFrame.from_dict(
                {
                    "zi": ["不", "不"],
                    "MC": ["pjut", "pjuw"],
                    "MCInitial": ["p-", "p-"],
                    "MCfinal": ["-jut", "-juw"],
                }
            )
        )
        self.assertEqual(rc.initial_for("不"), "p-")

    def test_final_for(self):
        """returns the final for a given character"""
        rc = Reconstruction(
            pd.DataFrame.from_dict(
                {
                    "zi": ["東"],
                    "MC": ["tuwng"],
                    "MCInitial": ["t-"],
                    "MCfinal": ["-uwng"],
                }
            )
        )
        self.assertEqual(rc.final_for("東"), "-uwng")

    def test_fanqie_reading_for(self):
        """returns the fanqie reading for a given initial and final char"""
        rc = Reconstruction(
            pd.DataFrame.from_dict(
                {
                    "zi": ["充", "忪", "為", "追", "尼"],
                    "MC": ["tsyhuwng", "tsyowng", "hjwe", "trwij", "nrij"],
                    "MCInitial": ["tsyh-", "tsy-", "hj-", "tr-", "nr-"],
                    "MCfinal": ["-juwng", "-jowng", "-jwe", "-wij", "-ij"],
                }
            )
        )
        # simple case
        self.assertEqual(rc.fanqie_reading_for("追", "忪"), "trjowng")
        # y + j = y
        self.assertEqual(rc.fanqie_reading_for("忪", "充"), "tsyuwng")
        # yh + j = yh
        self.assertEqual(rc.fanqie_reading_for("充", "忪"), "tsyhowng")
        # j + j = j
        self.assertEqual(rc.fanqie_reading_for("為", "充"), "hjuwng")
        # j + w = w
        self.assertEqual(rc.fanqie_reading_for("為", "追"), "hwij")
        # j + i = i
        self.assertEqual(rc.fanqie_reading_for("為", "尼"), "hij")
