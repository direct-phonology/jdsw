"""
Convert Tharsen & Wang's JDSW data to a format that can be read by prodigy.
"""

import jsonlines
import typer
import csv
import sys
import re
from pathlib import Path
from typing import List, Tuple, TypedDict, Dict

ASSETS_PATH = Path("assets")

# collapse some tags in tharsen & wang's schema
TAG_MAP = {
  "E": "E",     # headword
  "B": "T",     # book title
  "BC": "C",    # commentary on book title
  "F": "F",     # fanqie
  "T": "T",     # poem title
  "J": "T",     # juan number
  "C": "C",     # commentary on headword
  "CF": "F",    # fanqie reading for char in commentary
  "CC": "C",    # commentary on commentary
  "S": "T",     # section title
  "SC": "C",    # commentary on section title
  "SF": "F",    # fanqie reading for char in section title
  "SS": "T",    # sub-section title
  "SSC": "C",   # commentary on sub-section title
  "SSF": "F",   # fanqie reading for char in sub-section title
}

# see https://prodi.gy/docs/api-interfaces#spans
class ProdigyToken(TypedDict):
  text: str
  start: int
  end: int
  id: int
  ws: bool

class ProdigySpan(TypedDict):
  start: int
  end: int
  token_start: int
  token_end: int
  label: str

class ProdigySpancatTask(TypedDict):
  text: str
  tokens: List[ProdigyToken]
  spans: List[ProdigySpan]

# Basic monotonically-increasing integer ID generator for tokens
class Vocab:

  _id = 0
  _tok2id: Dict[str, int] = {}

  @classmethod
  def get(cls, key: str) -> int:
    if key not in cls._tok2id:
      cls._tok2id[key] = cls._id
      cls._id += 1
    return cls._tok2id[key]


# Monotonically-increasing unicode lookup for yijing hexagrams
# See https://en.wikipedia.org/wiki/Yijing_Hexagram_Symbols_(Unicode_block)
class Hexagrams:

  _codepoint = 0x4DC0 - 1

  @classmethod
  def next(cls, *_args) -> str:
    if cls._codepoint >= 0x4DFF:
      raise ValueError("no more hexagrams")
    cls._codepoint += 1
    return chr(cls._codepoint)


def main(in_path: Path = ASSETS_PATH / "tharsen_wang_jdsw.tsv") -> None:
  # read input .tsv format file; ignore BOM ("\ufeff")
  fp = in_path.open("r", encoding="utf-8-sig")
  reader = csv.reader(fp, delimiter="\t")

  # group examples by "E" tag (headwords)
  examples: List[List[Tuple[str, str]]] = [[]]
  current_example = 0
  for row in reader:
    try:
      tag, span = row
    except ValueError:
      continue
    if tag == "E":
      examples.append([])
      current_example += 1
    examples[current_example].append((tag, span))

  # convert to prodigy format and write to .jsonl file
  writer = jsonlines.Writer(sys.stdout)
  for example in examples:
    writer.write(eg_to_prodigy(example))

def eg_to_prodigy(eg: List[Tuple[str, str]]) -> ProdigySpancatTask:
  """Convert a single example to Prodigy format."""
  text: str = ""
  tokens: List[ProdigyToken] = []
  spans: List[ProdigySpan] = []

  for [tag, span] in eg:
    # remove any whitespace in both tag and span
    tag = "".join(tag.strip().split())
    span = "".join(span.strip().split())

    # convert yijing hexagram markers to their unicode characters
    span = re.sub(r"gua", Hexagrams.next, span)

    # ignore markers for non-representable characters, errors, etc. in text
    span = re.sub(r"（.）", "", span)
    span = re.sub(r"\(.\)", "", span)

    # remove any remaining english characters or punctuation
    span = re.sub(r"[a-zA-Z`]", "", span)

    # extract fanqie target markers and pre-add them as one-char spans
    target = span.find("_")
    if target != -1:
      target_token = len(text) + target - 1
      spans.append({
        "start": target_token,
        "end": target_token,
        "token_start": target_token,
        "token_end": target_token,
        "label": "FE",
      })
      span = span.replace("_", "")

    # calculate indices once so we don't do it in the loop
    span_start = len(text)
    span_end = span_start + len(span)

    # add the text to the example text and the tokens to the example tokens
    for j, char in enumerate(span):
      text += char
      tokens.append({
        "text": char,
        "start": span_start + j,
        "end": span_start + j,
        "id": Vocab.get(char),
        "ws": False,
      })

    # add the span to the example spans
    spans.append({
      "start": span_start,
      "end": span_end,
      "token_start": span_start,
      "token_end": span_end,
      "label": tag,
    })

  return {
    "text": text,
    "tokens": tokens,
    "spans": spans,
  }

main.__doc__ = __doc__

if __name__ == "__main__":
  typer.run(main)
