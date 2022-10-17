import re
from typing import Iterator
from xml.etree import ElementTree as ET

from pathlib import Path
from torch.utils.data import IterableDataset

from scripts.lib.documents import KanripoDoc


class KanripoDataset(IterableDataset):
    doc_id_re = re.compile(r"(?:KR|CH)\d\w\d{4}")


class KanripoTxtDataset(KanripoDataset):
    """
    Dataset of plaintext files from the Kanseki repository.

    Yields KanripoDocuments when iterated over by recursively searching the
    provided path for .txt files that include a Kanripo ID in their filename.
    """

    def __init__(self, path: str | Path) -> None:
        if isinstance(path, str):
            path = Path(path)
        self.path = path

    def __iter__(self) -> Iterator[KanripoDoc]:
        for file in self.path.glob("**/*.txt"):
            if self.doc_id_re.match(file.stem):
                yield KanripoDoc(
                    id=file.stem,
                    text=file.read_text(encoding="utf-8"),
                )


class KanripoXmlDataset(KanripoDataset):
    """
    Dataset of TEI-XML files from the Kanseki repository.

    Yields KanripoDocuments when iterated over by recursively searching the
    provided path for .xml files that include a Kanripo ID in their filename.
    """

    xmlns = {
        "tei": "http://www.tei-c.org/ns/1.0",
        "xml": "http://www.w3.org/XML/1998/namespace",
    }

    def __init__(self, path: str | Path) -> None:
        if isinstance(path, str):
            path = Path(path)
        self.path = path

    def __iter__(self) -> Iterator[KanripoDoc]:
        for file in self.path.glob("**/*.xml"):
            doc_id = self.doc_id_re.match(file.stem)
            if doc_id:
                tei = ET.parse(file).getroot()
                for i, juan in enumerate(
                    tei.findall("./tei:text/tei:body/tei:div", self.xmlns)
                ):
                    yield KanripoDoc(
                        id=f"{doc_id.group(0)}_{i + 1:03}",
                        text=ET.tostring(juan, encoding="unicode", method="text"),
                    )


# TODO: KanripoRemoteDataset?

__all__ = ["KanripoTxtDataset", "KanripoXmlDataset"]
