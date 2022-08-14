import re
from typing import Iterator

from pathlib import Path
from torch.utils.data import Dataset
from collections import defaultdict


class KanripoDataset(Dataset):
    """
    Dataset of documents from the Kanseki repository stored on a filesystem.

    Recursively loads all files from the given path with names that include
    Kanripo identifiers (e.g. KR1a0001). Files are loaded at access time when
    iterating, or can be accessed directly by keying on document ID.

    Joins documents that were split across multiple files: KR1a0001_001.txt,
    KR1a0001_002.txt, and so on will be joined into a single document with ID
    KR1a0001.

    Limits to txt files by default unless another `ext` is specified.
    """

    krid = re.compile(r"(KR|CH)\d\w\d{4}")

    def __init__(self, path: Path | str, ext: str = "txt") -> None:
        # allow passing a string or Path object
        self.path = path if isinstance(path, Path) else Path(path)

        # build a map of document IDs to files in that document
        self.docs = defaultdict(list)
        for file in self.path.glob(f"**/*{ext}"):
            docid = self.krid.search(file.name)
            if docid:
                self.docs[docid.group(0)].append(file)

    def __len__(self) -> int:
        return len(self.docs)

    def __contains__(self, docid: str) -> bool:
        return docid in self.docs

    def __getitem__(self, docid: str) -> str:
        # read all files in the document in order and join them into a string
        return "".join(
            (f.read_text(encoding="utf-8") for f in sorted(self.docs[docid]))
        )

    def __iter__(self) -> Iterator[str]:
        # for each document ordered by id, yield text of that document
        return (self[docid] for docid in sorted(self.docs))


# TODO: KanripoRemoteDataset?
