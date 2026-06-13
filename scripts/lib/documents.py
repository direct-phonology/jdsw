from typing import Any, Dict, Iterator, Optional

DocMeta = Dict[str, Any]


class KanripoDoc:
    """
    A single document from the Kanseki repository, corresponding to one juan.

    Stores a document identifier and the text of the document. String operations
    are supported and operate directly on the text of the document. Documents
    are ordered by their identifier. Arbitrary metadata can be stored as a dict
    at doc.meta.
    """

    def __init__(self, id: str, text: str, meta: Optional[DocMeta] = None) -> None:
        self.id = id
        self.text = text
        self.meta = dict(meta) if meta else {}

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


def merge_docs(*docs: KanripoDoc, meta: Optional[DocMeta] = None) -> KanripoDoc:
    """
    Merge multiple documents into a single document.

    An identifier is generated for the new document by concatenating the first
    and last identifiers of the documents being merged. The text of all
    documents is merged together.

    Layer spans (meta["layers"]) and the embedded-JDSW segments
    (meta["jdsw_self"]) are carried across: each part's spans are offset by the
    running length of the text merged so far, and abutting same-label layer
    spans are coalesced across the part boundary. Preserving layers keeps
    layer-aware reading extraction (注同 scope, layer_at) working under
    per-work alignment, where a work's fascicles are merged before aligning.

    Any explicit meta provided is used as the base for the merged metadata, so
    other caller-supplied keys (e.g. "title") survive. The "layers"/"jdsw_self"
    keys are written only when at least one source doc carried that key, so a
    merge of docs with no layer signal does not fabricate empty ones.
    """

    # ensure they're ordered by id
    _docs = list(sorted(docs))

    # bail out if there's nothing to merge
    if len(_docs) < 1:
        raise ValueError("Must provide at least one document to merge")

    layers: list[list] = []
    jdsw_self: list = []
    offset = 0
    for doc in _docs:
        for start, end, label in doc.meta.get("layers", []):
            span = [start + offset, end + offset, label]
            # coalesce with the previous span when they abut and share a label
            if layers and layers[-1][2] == label and layers[-1][1] == span[0]:
                layers[-1][1] = span[1]
            else:
                layers.append(span)
        for pos, text in doc.meta.get("jdsw_self", []):
            jdsw_self.append((pos + offset, text))
        offset += len(doc.text)

    merged_meta = dict(meta) if meta else {}
    if any("layers" in doc.meta for doc in _docs):
        merged_meta["layers"] = [tuple(span) for span in layers]
    if any("jdsw_self" in doc.meta for doc in _docs):
        merged_meta["jdsw_self"] = jdsw_self

    # generate a new id and merge the text
    return KanripoDoc(
        id=f"{_docs[0].id}-{_docs[-1].id}",
        text="".join(doc.text for doc in _docs),
        meta=merged_meta,
    )
