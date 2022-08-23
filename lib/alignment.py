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
