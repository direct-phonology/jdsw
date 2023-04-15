from unittest import TestCase, skip

from scripts.bin.convert_tw import ProdigyTask

@skip("WIP")
class TestProdigyConversion(TestCase):

  def setUp(self) -> None:
    self.data = [
      ("E", "竄"),
      ("F", "七亂反"),
      ("C", "徐_又"),
      ("F", "七外反"),
      ("C", "逃也"),
    ]
    self.task = ProdigyTask(self.data)

  def test_task_text(self) -> None:
    self.assertEqual(self.task.text, "竄七亂反徐又七外反逃也")

  def test_task_tokens(self) -> None:
    self.assertEqual(self.task.tokens, [
      {"text": "竄", "start": 0, "end": 1, "id": 0},
      {"text": "七", "start": 1, "end": 2, "id": 1},
      {"text": "亂", "start": 2, "end": 3, "id": 2},
      {"text": "反", "start": 3, "end": 4, "id": 3},
      {"text": "徐", "start": 4, "end": 5, "id": 4},
      {"text": "又", "start": 5, "end": 6, "id": 5},
      {"text": "七", "start": 6, "end": 7, "id": 1},
      {"text": "外", "start": 7, "end": 8, "id": 7},
      {"text": "反", "start": 8, "end": 9, "id": 3},
      {"text": "逃", "start": 9, "end": 10, "id": 9},
      {"text": "也", "start": 10, "end": 11, "id": 10},
    ])

  def test_task_spans(self) -> None:
    self.assertEqual(self.task.spans, [
      {"start": 0, "end": 1, "token_start": 0, "token_end": 1, "label": "E"},
      {"start": 1, "end": 4, "token_start": 1, "token_end": 4, "label": "F"},
      {"start": 4, "end": 6, "token_start": 4, "token_end": 6, "label": "C"},
      {"start": 6, "end": 9, "token_start": 6, "token_end": 9, "label": "F"},
      {"start": 9, "end": 11, "token_start": 9, "token_end": 11, "label": "C"},
     ])

  def test_task_rels(self) -> None:
    self.assertEqual(self.task.rels, [
      {"child": 0, "head": 3, "label": "fanqie"},
      {"child": 4, "head": 8, "label": "fanqie"},
      {"child": 4, "head": 8, "label": "C"},
      {"child": 3, "head": 4, "label": "F"},
      {"child": 4, "head": 5, "label": "C"},
    ])
