import csv
import re

from fastcore.transform import Transform

from scripts.lib.documents import KanripoDoc


class DocTextTransform(Transform):
    def encodes(self, doc: KanripoDoc) -> KanripoDoc:
        doc.text = self.encodes(doc.text)  # type: ignore[assignment,arg-type]
        return doc


class DocMetaTransform(Transform):
    key: str

    def encodes(self, doc: KanripoDoc) -> KanripoDoc:
        text, value = self.encodes(doc.text)  # type: ignore[assignment,arg-type]
        doc.text = text
        doc.meta[self.key] = value
        return doc


class RemoveComments(DocTextTransform):
    comment_re = re.compile(r"^#.+", flags=re.MULTILINE)

    def encodes(self, text: str) -> str:  # type: ignore[override]
        return self.comment_re.sub("", text)


class RemovePageBreaks(DocTextTransform):
    pb_re = re.compile(r"<pb:(?:.+)>")

    def encodes(self, text: str) -> str:  # type: ignore[override]
        return self.pb_re.sub("", text)


class RemoveWhitespace(DocTextTransform):
    def encodes(self, text: str) -> str:  # type: ignore[override]
        return "".join(text.split())


class RemoveChars(DocTextTransform):
    def __init__(self, chars: str) -> None:
        self.encoder = str.maketrans(dict((c, "") for c in chars))

    def encodes(self, text: str) -> str:  # type: ignore[override]
        return str.translate(text, self.encoder)


class HealAnnotations(DocTextTransform):
    def encodes(self, text: str) -> str:  # type: ignore[override]
        return text.replace(")(", "").replace("/", "")


class KanripoUnicode(DocTextTransform):
    entity_re = re.compile(r"&(KR\d+);|(\[.+?\])")

    def __init__(self) -> None:
        reader = csv.DictReader(open("data/kr-unicode.csv", encoding="utf-8"))
        self.encoder = dict(((row["form"], row["unicode"]) for row in reader))

    def encodes(self, text: str) -> str:  # type: ignore[override]
        return self.entity_re.sub(self._encode_one, text)

    def _encode_one(self, match: re.Match) -> str:
        text = match.group(1) or match.group(2)
        return self.encoder.get(text, text)


class ExtractTitle(DocMetaTransform):
    key = "title"

    def encodes(self, text: str) -> str:  # type: ignore[override]
        pass


class ExtractAnnotations(DocMetaTransform):
    key = "annotations"
    anno_re = re.compile(r"(?P<headword>.+?)\((?P<annotation>.+?)\)")

    def encodes(self, text: str) -> tuple[str, dict]:  # type: ignore[override]
        annotations = {}
        cleaned_text = ""
        for headword, annotation in self.anno_re.findall(text):
            bounds = (len(cleaned_text), len(cleaned_text) + len(headword))
            annotations[bounds] = annotation
            cleaned_text += headword
        return cleaned_text, annotations
