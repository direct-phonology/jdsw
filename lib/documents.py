from typing import Iterator, Dict, Any

DocMeta = Dict[str, Any]


class KanripoDoc:
    """
    A single document from the Kanseki repository, corresponding to one juan.

    Stores a document identifier and the text of the document. String operations
    are supported and operate directly on the text of the document. Documents
    are ordered by their identifier. Arbitrary metadata can be stored as a dict
    at doc.meta.
    """

    def __init__(self, id: str, text: str, meta: DocMeta = {}) -> None:
        self.id = id
        self.text = text
        self.meta = meta.copy()

    def __repr__(self) -> str:
        return f'KanripoDoc(id="{self.id}", text="{self.text}")'

    def __str__(self) -> str:
        return self.text

    def __len__(self) -> int:
        return len(self.text)

    def __getitem__(self, index: int) -> str:
        return self.text[index]

    def __iter__(self) -> Iterator[str]:
        return iter(self.text)

    def __contains__(self, string: str) -> bool:
        return string in self.text

    def __lt__(self, other: "KanripoDoc") -> bool:
        return self.id < other.id
