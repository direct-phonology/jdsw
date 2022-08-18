import re
from typing import Iterator
from xml.etree import ElementTree as ET

from pathlib import Path
from torch.utils.data import IterableDataset

from lib.documents import KanripoDoc


class KanripoTxtDataset(IterableDataset):
    """
    Dataset of plaintext files from the Kanseki repository.

    Yields KanripoDocuments when iterated over by recursively searching the
    provided path for .txt files that include a Kanripo ID in their filename.
    """

    doc_id_re = re.compile(r"((?:KR|CH)\d\w\d{4})_(\d{3})")

    def __init__(self, path: str) -> None:
        self.path = Path(path)

    def __iter__(self) -> Iterator[KanripoDoc]:
        for file in self.path.glob("**/*.txt"):
            doc_id = self.doc_id_re.match(file.stem)
            if doc_id:
                yield KanripoDoc(
                    id=doc_id.group(0),
                    text=file.read_text(encoding="utf-8"),
                )


class KanripoXmlDataset(IterableDataset):
    """
    Dataset of TEI-XML files from the Kanseki repository.

    Yields KanripoDocuments when iterated over by recursively searching the
    provided path for .xml files that include a Kanripo ID in their filename.
    """

    doc_id_re = re.compile(r"((?:KR|CH)\d\w\d{4})")
    xmlns = {
        "tei": "http://www.tei-c.org/ns/1.0",
        "xml": "http://www.w3.org/XML/1998/namespace",
    }

    def __init__(self, path: str) -> None:
        self.path = Path(path)

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
