import csv
import subprocess
import pathlib

# create temporary output file for test
tmp_file = pathlib.Path("tmp", "test.csv")
tmp_file.parent.mkdir(parents=True, exist_ok=True)

# run alignjdsw on the first chapter of the lunyu and output to temp file
with tmp_file.open("w", encoding="utf-8") as fh:
  subprocess.run(
    [
      pathlib.Path("bin/alignjdsw.py"),
      pathlib.Path("src/jdsw/lunyu/001.txt"),
      pathlib.Path("src/sbck/lunyu/001.txt"),
    ],
    stdout=fh
  )

# compare the actual output to the expected output
expected = csv.DictReader(open("bin/tests/fixtures/lunyu_001.csv", encoding="utf-8"))
actual = csv.DictReader(open(tmp_file, encoding="utf-8"))
for expected_row, actual_row in zip(expected, actual):
  assert actual_row["location"] == expected_row["location"]

# delete temporary file when done
tmp_file.unlink()
