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
        reader = csv.DictReader(open("assets/kr-unicode.csv", encoding="utf-8"))
        self.encoder = dict(((row["form"], row["unicode"]) for row in reader))

    def encodes(self, text: str) -> str:  # type: ignore[override]
        return self.entity_re.sub(self._encode_one, text)

    def _encode_one(self, match: re.Match) -> str:
        text = match.group(1) or match.group(2)
        return self.encoder.get(text, text)


class ExtractLayers(Transform):
    """
    Strip the parenthesized commentary markup of an SBCK-style edition while
    recording which layer each character of the cleaned text belongs to.

    doc.meta["layers"] holds coalesced (start, end, label) spans over the
    cleaned text, where label is "main" or "commentary". Text from a 〇
    marker to the end of its paren group is Lu Deming's own 音義 embedded in
    the edition (e.g. SBCK 公羊解詁 KR1e0007, where a group reads 注〇音義 or
    is 〇-initial outright); the JDSW must not be aligned against its own
    text, so these segments are removed from the cleaned text entirely and
    recorded under doc.meta["jdsw_self"] as (position, text) pairs, where
    position is the offset in the cleaned text at which the segment sat.
    Run after HealAnnotations, so groups split at page breaks are rejoined
    and a marker is not severed from its segment.
    """

    MAIN = "main"
    COMMENTARY = "commentary"
    JDSW_SELF = "jdsw_self"
    # the transcription uses 〇 (U+3007) and ○ (U+25CB) interchangeably; inside
    # a paren group a circle opens the JDSW's own embedded 音義, while at paren
    # depth 0 the same glyph is a 經-entry separator and is simply dropped
    OPEN, CLOSE, MARKER = "(（", ")）", "〇○"

    def encodes(self, doc: KanripoDoc) -> KanripoDoc:
        text, layers, jdsw_self = self.extract(doc.text)
        doc.text = text
        doc.meta["layers"] = layers
        doc.meta["jdsw_self"] = jdsw_self
        return doc

    def extract(self, text: str) -> tuple[str, list, list]:
        cleaned: list[str] = []
        layers: list[list] = []
        jdsw_self: list[tuple[int, str]] = []
        depth = 0
        group: list[str] = []  # chars of the current top-level paren group

        def emit(char: str, label: str) -> None:
            pos = len(cleaned)
            cleaned.append(char)
            if layers and layers[-1][2] == label and layers[-1][1] == pos:
                layers[-1][1] = pos + 1
            else:
                layers.append([pos, pos + 1, label])

        def close_group() -> None:
            chars = "".join(group)
            cut = min(
                (i for i in (chars.find(m) for m in self.MARKER) if i != -1),
                default=len(chars),
            )
            for char in chars[:cut]:
                emit(char, self.COMMENTARY)
            if cut < len(chars):
                jdsw_self.append((len(cleaned), chars[cut:]))
            group.clear()

        for char in text:
            if char in self.OPEN:
                depth += 1
            elif char in self.CLOSE:
                depth = max(depth - 1, 0)
                if depth == 0:
                    close_group()
            elif depth > 0:
                group.append(char)
            elif char in self.MARKER:
                continue  # 經-entry separator in the main flow
            else:
                emit(char, self.MAIN)
        close_group()  # tolerate an unterminated group at end of text

        return "".join(cleaned), [tuple(span) for span in layers], jdsw_self


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
