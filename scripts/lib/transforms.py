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
    cleaned text. Inside a paren group, text from the first embedded-音義
    marker to the end of the group is Lu Deming's own 音義 carried by the
    edition; the JDSW must not be aligned against its own text, so those
    segments are removed and recorded under doc.meta["jdsw_self"] as
    (position, text) pairs (position = offset in the cleaned text where the
    segment sat). The markers are:

    - a circle, 〇 (U+3007) or ○ (U+25CB), used interchangeably in the SBCK
      公羊解詁 (KR1e0007), where a group reads 注〇音義 or is circle-initial;
    - the phrase 音義曰, which opens the 篇-initial 音義 block in the SBCK
      莊子 (KR5c0051), where later blocks instead use a circle.

    The remaining characters are labeled "commentary" (inside parens) or
    "main" (outside). A witness with no paren markup at all — the ZTDZ 老子
    (KR5c0073) writes 經 and 王弼注 full-size and undelimited — yields no
    layer signal; rather than mislabel everything "main", such a doc is
    labeled entirely "unknown" (see docs/corpus.md on the positional
    heuristic that would replace this).

    Run after HealAnnotations, so groups split at page breaks are rejoined
    and a marker is not severed from its segment.
    """

    MAIN = "main"
    COMMENTARY = "commentary"
    UNKNOWN = "unknown"
    JDSW_SELF = "jdsw_self"
    OPEN, CLOSE = "(（", ")）"
    SEPARATORS = "〇○"  # circles at paren depth 0 are 經-entry separators
    SELF_MARKERS = ("〇", "○", "音義曰")  # open Lu's embedded 音義 inside a group

    def encodes(self, doc: KanripoDoc) -> KanripoDoc:
        text, layers, jdsw_self = self.extract(doc.text)
        doc.text = text
        doc.meta["layers"] = layers
        doc.meta["jdsw_self"] = jdsw_self
        return doc

    def _self_marker_cut(self, chars: str) -> int:
        """Index of the earliest embedded-音義 marker in a group, or len."""
        return min(
            (i for i in (chars.find(m) for m in self.SELF_MARKERS) if i != -1),
            default=len(chars),
        )

    def extract(self, text: str) -> tuple[str, list, list]:
        cleaned: list[str] = []
        layers: list[list] = []
        jdsw_self: list[tuple[int, str]] = []
        depth = 0
        saw_commentary = False
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
            cut = self._self_marker_cut(chars)
            for char in chars[:cut]:
                emit(char, self.COMMENTARY)
            if cut < len(chars):
                jdsw_self.append((len(cleaned), chars[cut:]))
            group.clear()

        for char in text:
            if char in self.OPEN:
                depth += 1
                saw_commentary = True
            elif char in self.CLOSE:
                depth = max(depth - 1, 0)
                if depth == 0:
                    close_group()
            elif depth > 0:
                group.append(char)
            elif char in self.SEPARATORS:
                continue  # 經-entry separator in the main flow
            else:
                emit(char, self.MAIN)
        close_group()  # tolerate an unterminated group at end of text

        # no commentary markup at all: we cannot tell 經 from 注, so the
        # "main" labels are not trustworthy — mark the whole witness unknown
        if not saw_commentary:
            for span in layers:
                span[2] = self.UNKNOWN

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
