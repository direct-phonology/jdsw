import re
import csv
import spacy
import itertools

from fastcore.transform import Transform


@Transform
def remove_comments(text: str) -> str:
    return re.sub(r"^#.+", "", text, flags=re.MULTILINE)


@Transform
def remove_page_breaks(text: str) -> str:
    return re.sub(r"<pb:(?:.+)>", "", text)


@Transform
def remove_pilcrows(text: str) -> str:
    return text.replace("¶", "")


@Transform
def remove_empty_lines(text: str) -> str:
    return re.sub(r"\n{2,}", "\n", text).strip()


@Transform
def remove_whitespace(text: str) -> str:
    return "".join(text.split())


@Transform
def smooth_annotations(text: str) -> str:
    return text.replace(")(", "").replace("/", "")


class KanripoUnicode(Transform):
    def __init__(self) -> None:
        reader = csv.DictReader(open("data/kr-unicode.csv", encoding="utf-8"))
        self.encoder = dict(((row["form"], row["unicode"]) for row in reader))
        self.decoder = str.maketrans(dict(((v, k) for k, v in self.encoder.items())))

    def encodes(self, text: str) -> str:
        return re.sub(r"&(KR\d+);|(\[.+?\])", self._encode, text)

    def decodes(self, text: str) -> str:
        return str.translate(text, self.decoder)

    def _encode(self, match: re.Match) -> str:
        text = match.group(1) or match.group(2)
        return self.encoder.get(text, text)


class SplitAnnotations(Transform):
    def encodes(self, text: str) -> list:
        parts = re.split(r"(.+?)\(.+?\)", text)
        return list(itertools.zip_longest(parts[::2], parts[1::2], fillvalue=""))

    def decodes(self, pairs: list) -> str:
        return "".join(f"{text}{note}" for text, note in pairs)


class SplitSentences(Transform):
    def __init__(self, nlp: spacy.Language, lang: str = None) -> None:
        if not nlp and not lang:
            raise ValueError("A model or language code must be provided")
        self.nlp = nlp or spacy.blank(lang)  # type: ignore

    def encodes(self, text: str) -> list:
        return [sent.text for sent in self.nlp(text).sents]

    def decodes(self, sentences: list) -> str:
        return "".join(sentences)


class RemovePunctuation(Transform):
    def __init__(self, nlp: spacy.Language, lang: str = None) -> None:
        if not nlp and not lang:
            raise ValueError("A model or language code must be provided")
        self.nlp = nlp or spacy.blank(lang)  # type: ignore

    def encodes(self, text: str) -> str:
        return "".join([tok.text for tok in self.nlp(text) if not tok.is_punct])
