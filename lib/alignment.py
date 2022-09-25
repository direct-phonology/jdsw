import json
from difflib import Differ
from pathlib import Path

from lib.documents import KanripoDoc

VARIANTS = str.maketrans(
    json.loads(Path("data/variants.json").read_text(encoding="utf-8"))
)


class Alignment:
    gap_char = "　"

    def __init__(self, x: KanripoDoc, y: KanripoDoc) -> None:
        self.x, self.y = x, y
        self.diff = list(
            Differ().compare(
                self.x.text.translate(VARIANTS),
                self.y.text.translate(VARIANTS),
            )
        )

    def __repr__(self) -> str:
        return f'Alignment(x="{self.x.id}", y="{self.y.id}")'

    def __str__(self) -> str:
        x_aligned = [c[2] if c[0] in [" ", "-"] else self.gap_char for c in self.diff]
        y_aligned = [c[2] if c[0] in [" ", "+"] else self.gap_char for c in self.diff]
        return f"{self.x.id}:\t{''.join(x_aligned)}\n{self.y.id}:\t{''.join(y_aligned)}"

    def align_annotations(self) -> "Alignment":
        # bail out if there's nothing to align from
        if not self.y.meta.get("annotations"):
            return self

        # create a mapping of indices in y to indices in x
        y_to_x: dict[int, int] = {}
        x_idx = y_idx = 0
        for c in self.diff:
            if c[0] == "+":
                y_idx += 1
            elif c[0] == "-":
                x_idx += 1
            else:
                y_to_x[y_idx] = x_idx
                x_idx += 1
                y_idx += 1

        # clear out any metadata in x that we're going to overwrite
        self.x.meta["annotations"] = {}

        # map all metadata values in y with corresponding locations in x to x
        for y_idx, value in self.y.meta["annotations"].items():
            if map_to := y_to_x.get(y_idx):
                self.x.meta["annotations"][map_to] = value

        return self
