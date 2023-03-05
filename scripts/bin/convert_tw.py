"""
Convert Tharsen & Wang's JDSW data to a format that can be read by prodigy.
"""

import jsonlines
import typer
import csv
import sys
import re
from pathlib import Path
from typing import List, Tuple, Dict, Sequence

ASSETS_PATH = Path("assets")

# TODO: collapse some tags in tharsen & wang's schema
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
class ProdigyToken:
  text: str
  start: int
  id: int
  ws: bool

  def __init__(self, text: str, start: int, id: int) -> None:
    self.text = text
    self.start = start
    self.id = id

  @property
  def end(self) -> int:
    return self.start + len(self.text)

  def as_dict(self) -> Dict:
    return {
      "text": self.text,
      "start": self.start,
      "end": self.end,
      "id": self.id,
      "ws": False,
    }

class ProdigySpan:
  tokens: Sequence[ProdigyToken]
  label: str

  def __init__(self, tokens: Sequence[ProdigyToken], label: str) -> None:
    self.label = label
    self.tokens = tokens

  @property
  def start(self) -> int:
    return self.tokens[0].start

  @property
  def end(self) -> int:
    return self.tokens[-1].end

  @property
  def token_end(self) -> int:
    return self.token_start + len(self.tokens)

  def as_dict(self) -> Dict:
    return {
      "start": self.start,
      "end": self.end,
      "token_start": self.token_start,
      "token_end": self.token_end,
      "label": self.label,
    }

class ProdigyRelation:
  child: int
  head: int
  label: str

class ProdigyTask:
  tokens: List[ProdigyToken]
  spans: List[ProdigySpan]
  relations: List[ProdigyRelation]

  def add_token(self, text: str) -> None:
    self.tokens.append(ProdigyToken(text, len(self.tokens), Vocab.get(text)))

  def add_span(self, start: int, len: int, label: str) -> None:
    self.spans.append(ProdigySpan(start, len, label))

  def add_span(self, text: str, label: str) -> None:
    start_token = len(self.tokens)
    for i, c in enumerate(text):
      self.tokens.append(ProdigyToken(c, start_token + i, Vocab.get(c)))
    self.spans.append(ProdigySpan(start_token, label, self.tokens[start_token:]))

  def add_rel(self, child: int, head: int, label: str) -> None:
    self.relations.append(ProdigyRelation(child, head, label))

  def __init__(self, text: str) -> None:
    self.tokens = [ProdigyToken(c, i, Vocab.get(c)) for i, c in enumerate(text)]

  @property
  def text(self) -> str:
    return "".join(t.text for t in self.tokens)

  # Process for converting _ to rel:
  # 


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

def eg_to_prodigy(eg: List[Tuple[str, str]]) -> ProdigyTask:
  """Convert a single example to Prodigy format."""
  text: str = ""
  tokens: List[ProdigyToken] = []
  spans: List[ProdigySpan] = []
  relations: List[ProdigyRelation] = []

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

    # extract fanqie target markers and pre-add them as relations
    target = span.find("_")
    if target != -1:
      target_token = len(text) + target - 1
      relations.append({
        "child": target_token,
        "label": "fanqie",
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
    "relations": relations,
  }

main.__doc__ = __doc__

if __name__ == "__main__":
  typer.run(main)
