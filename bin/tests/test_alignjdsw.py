import csv
import pathlib
import subprocess
import unittest

FIXTURE_PATH = "bin/tests/fixtures/lunyu_001.csv"

@unittest.skip("FIXME")
class TestAlignJDSW(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # create temporary output file for test
        cls.tmp_file = pathlib.Path("tmp", "test.csv")
        cls.tmp_file.parent.mkdir(parents=True, exist_ok=True)

        # run alignjdsw on the first chapter of the lunyu and output to temp file
        with cls.tmp_file.open("w", encoding="utf-8") as fh:
            subprocess.run(
                [
                    pathlib.Path("bin/alignjdsw.py"),
                    pathlib.Path("out/csv/jdsw/lunyu/001.csv"),
                    pathlib.Path("out/csv/sbck/lunyu/001.csv"),
                ],
                stdout=fh,
            )

    def test_locations(self):
        # compare the actual output to the expected output
        expected = csv.DictReader(open(FIXTURE_PATH, encoding="utf-8"))
        actual = csv.DictReader(open(self.tmp_file, encoding="utf-8"))
        for exp, act in zip(expected, actual):
            with self.subTest(text=exp["source"], note=exp["note"]):
                self.assertEqual(
                    act["location"],
                    exp["location"],
                    msg=f"expected {exp['source']} in {exp['location']}, got {act['location']}",
                )

    @classmethod
    def tearDownClass(cls):
        # delete temporary file when done
        cls.tmp_file.unlink()
