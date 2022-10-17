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


def merge_docs(*docs: KanripoDoc, meta: DocMeta = {}) -> KanripoDoc:
    """
    Merge multiple documents into a single document.

    An identifier is generated for the new document by concatenating the first
    and last identifiers of the documents being merged. The text of all documents
    are merged together. Metadata is not merged; instead, it can be provided
    when merging as with a single document.
    """

    # ensure they're ordered by id
    _docs = list(sorted(docs))

    # bail out if there's nothing to merge
    if len(_docs) < 1:
        raise ValueError("Must provide at least one document to merge")

    # generate a new id and merge the text
    return KanripoDoc(
        id=f"{_docs[0].id}-{_docs[-1].id}",
        text="".join(doc.text for doc in _docs),
        meta=meta.copy(),
    )
