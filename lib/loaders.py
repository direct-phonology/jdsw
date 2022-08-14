import re
from typing import Iterator
from xml.etree import ElementTree as ET

from pathlib import Path
from torch.utils.data import Dataset
from collections import defaultdict


class KanripoDataset(Dataset):
    krid = re.compile(r"(KR|CH)\d\w\d{4}")

class KanripoLocalDataset(KanripoDataset):
    """
    Dataset of documents from the Kanseki repository stored on a filesystem.

    Recursively loads all files from the given path with names that include
    Kanripo identifiers (e.g. KR1a0001). Files are loaded at access time when
    iterating, or can be accessed directly by keying on document ID.

    If merge = True, joins documents that were split across multiple files: 
    KR1a0001_001, KR1a0001_002, and so on will be joined into a single 
    document with ID KR1a0001.
    """
    ext: str

    def __init__(self, path: Path | str, merge: bool = False) -> None:
        # allow passing a string or Path object
        self.path = path if isinstance(path, Path) else Path(path)
        self.merge = merge

        # build a map of document IDs to files in that document
        self.docs = defaultdict(list)
        for file in self.path.glob(f"**/*{self.ext}"):
            docid = self.krid.search(file.name)
            if docid:
                self.docs[docid.group(0)].append(file)

    def __len__(self) -> int:
        return len(self.docs)

    def __contains__(self, docid: str) -> bool:
        return docid in self.docs

    def __getitem__(self, docid: str) -> list[Path]:
        return self.docs[docid]

class KanripoTxtDataset(KanripoLocalDataset):
    ext = "txt"

    def __iter__(self) -> Iterator[str]:
        for docid in sorted(self.docs):
            if self.merge:
                yield "".join((f.read_text(encoding="utf-8") for f in sorted(self[docid])))
            else:
                for f in sorted(self[docid]):
                    yield f.read_text(encoding="utf-8")

class KanripoXmlDataset(KanripoLocalDataset):
    ext = "xml"
    ns = {
        "tei": "http://www.tei-c.org/ns/1.0",
        "xml": "http://www.w3.org/XML/1998/namespace",
    }

    def __iter__(self) -> Iterator[ET.Element]:
        for docid in sorted(self.docs):
            contents = "".join((f.read_text(encoding="utf-8") for f in sorted(self[docid])))
            tei = ET.fromstring(contents)
            if self.merge:
                for doc in tei.findall("./tei:text/tei:body", self.ns):
                    yield doc
            else:
                for juan in tei.findall("./tei:text/tei:body/tei:div", self.ns):
                    yield juan



# TODO: KanripoRemoteDataset?
