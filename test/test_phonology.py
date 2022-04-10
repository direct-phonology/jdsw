from unittest import TestCase

import pandas as pd

from lib.phonology import Reconstruction, NoReadingError, MultipleReadingsError


class TestReconstruction(TestCase):
    def test_init(self):
        """dedupes input table on init"""
        pass

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
