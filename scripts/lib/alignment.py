"""
Align Jingdian Shiwen lemmata (headwords) to positions in a source text.

The JDSW quotes its headwords in the order they occur in the text it comments
on, so a correct alignment must be monotonic: if lemma B follows lemma A in the
JDSW, B's position in the source text must follow A's. The algorithm exploits
this directly:

1. Candidate enumeration: every exact occurrence of every (variant-normalized)
   lemma in the (variant-normalized) source text becomes a candidate, weighted
   by the square of its length. Multi-character matches are heavy anchors;
   single characters are cheap and ignorable.
2. Weighted longest-increasing-subsequence: choose at most one candidate per
   lemma such that positions are strictly increasing and non-overlapping and
   total weight is maximal. O(C log C) over C candidates, deterministic.
3. Gap-filling: lemmata not selected as anchors are searched for only in the
   window between their flanking anchors, first as exact matches, then by
   their longest matching prefix or suffix.
"""

from bisect import bisect_right
from dataclasses import dataclass
from itertools import groupby
from typing import Optional

from scripts.lib.documents import KanripoDoc
from scripts.lib.variants import normalize

# alignment confidence levels, from best to worst
ANCHOR = "anchor"  # exact match selected by weighted LIS
GAP = "gap"  # exact match found between two anchors
PARTIAL = "partial"  # prefix/suffix match found between two anchors
UNMATCHED = "unmatched"  # no plausible position found


@dataclass
class Match:
    """The aligned position of a single lemma in the source text."""

    index: int  # position of the lemma in the input sequence
    lemma: str
    start: Optional[int]  # span in the source text, if found
    end: Optional[int]
    confidence: str

    @property
    def found(self) -> bool:
        return self.start is not None


@dataclass
class _Candidate:
    lemma_index: int
    start: int
    end: int
    weight: int


class _MaxFenwick:
    """Fenwick tree over prefix maxima of (score, -candidate_index) pairs."""

    EMPTY = (0, 1)

    def __init__(self, size: int) -> None:
        self.tree = [self.EMPTY] * (size + 1)

    def update(self, i: int, value: tuple) -> None:
        i += 1
        while i < len(self.tree):
            self.tree[i] = max(self.tree[i], value)
            i += i & -i

    def query(self, i: int) -> tuple:
        """Maximum value over indices [0, i]."""
        i += 1
        best = self.EMPTY
        while i > 0:
            best = max(best, self.tree[i])
            i -= i & -i
        return best


def _find_all(needle: str, haystack: str, limit: int) -> list[int]:
    """All start offsets of needle in haystack, up to limit occurrences."""
    positions = []
    pos = haystack.find(needle)
    while pos != -1 and len(positions) <= limit:
        positions.append(pos)
        pos = haystack.find(needle, pos + 1)
    return positions


def _select_anchors(candidates: list[_Candidate]) -> list[_Candidate]:
    """
    Maximum-weight subsequence of candidates that is strictly increasing in
    both lemma order and (non-overlapping) text position.
    """
    if not candidates:
        return []

    # compress candidate end positions for the Fenwick tree
    ends = sorted({c.end for c in candidates})
    tree = _MaxFenwick(len(ends))

    scores = [0] * len(candidates)
    parents = [-1] * len(candidates)

    # group by lemma: query all of a lemma's candidates before inserting any,
    # so that no two candidates of the same lemma can chain together
    for _, group in groupby(enumerate(candidates), key=lambda c: c[1].lemma_index):
        group = list(group)
        for i, candidate in group:
            # best chain among candidates ending at or before this one starts
            slot = bisect_right(ends, candidate.start) - 1
            best_score, neg_index = (
                tree.query(slot) if slot >= 0 else _MaxFenwick.EMPTY
            )
            scores[i] = best_score + candidate.weight
            parents[i] = -neg_index if neg_index != 1 else -1
        for i, candidate in group:
            tree.update(bisect_right(ends, candidate.end) - 1, (scores[i], -i))

    # walk back from the best-scoring candidate to recover the chain
    best = max(range(len(candidates)), key=lambda i: (scores[i], -i))
    chain = []
    while best != -1:
        chain.append(candidates[best])
        best = parents[best]
    return list(reversed(chain))


def _fill_gap(
    lemma: str, text: str, window_start: int, window_end: int
) -> Optional[Match]:
    """Place a non-anchor lemma within the window between its flanking anchors."""
    window = text[window_start:window_end]

    # exact match within the window
    pos = window.find(lemma)
    if pos != -1:
        start = window_start + pos
        return Match(-1, lemma, start, start + len(lemma), GAP)

    # longest prefix or suffix match, extended to the full lemma length
    for length in range(len(lemma) - 1, 0, -1):
        pos = window.find(lemma[:length])
        if pos != -1:
            start = window_start + pos
            return Match(-1, lemma, start, min(start + len(lemma), window_end), PARTIAL)
        pos = window.find(lemma[-length:])
        if pos != -1:
            end = window_start + pos + length
            return Match(-1, lemma, max(end - len(lemma), window_start), end, PARTIAL)

    return None


def align_sequence(
    lemmas: list[str], text: str, max_candidates: int = 128
) -> list[Match]:
    """
    Align an ordered sequence of lemmata against a text, returning one Match
    per lemma. Lemmata occurring more than max_candidates times are excluded
    from anchor selection and placed by gap-filling only.
    """
    text_norm = normalize(text)
    lemmas_norm = [normalize(lemma) for lemma in lemmas]

    candidates = []
    for i, lemma in enumerate(lemmas_norm):
        positions = _find_all(lemma, text_norm, max_candidates)
        if 0 < len(positions) <= max_candidates:
            weight = len(lemma) ** 2
            for pos in positions:
                candidates.append(_Candidate(i, pos, pos + len(lemma), weight))

    anchors = {
        c.lemma_index: Match(c.lemma_index, lemmas[c.lemma_index], c.start, c.end, ANCHOR)
        for c in _select_anchors(candidates)
    }

    # fill the gaps between anchors, keeping placements monotonic
    matches = []
    cursor = 0
    anchor_indices = sorted(anchors)
    for i, lemma in enumerate(lemmas_norm):
        if i in anchors:
            matches.append(anchors[i])
            cursor = anchors[i].end
            continue

        # window extends to the next anchor, or the end of the text
        next_anchor = next((j for j in anchor_indices if j > i), None)
        window_end = anchors[next_anchor].start if next_anchor is not None else len(text_norm)

        match = _fill_gap(lemma, text_norm, cursor, window_end)
        if match:
            match.index, match.lemma = i, lemmas[i]
            matches.append(match)
            cursor = match.end
        else:
            matches.append(Match(i, lemmas[i], None, None, UNMATCHED))

    return matches


def layer_at(layers: list, position: int) -> str:
    """Edition layer ("main", "commentary", ...) containing a text position."""
    for start, end, label in layers:
        if start <= position < end:
            return label
    return "main"


class Alignment:
    """
    Aligns annotations from doc y onto doc x, where y's text is the
    concatenation of JDSW headwords and y.meta["annotations"] maps headword
    spans in y to annotation strings.

    After align_annotations(), x.meta["annotations"] maps spans in x to the
    transferred annotations, and x.meta["alignment"] holds a per-lemma report
    including match confidence and edition layer.
    """

    def __init__(self, x: KanripoDoc, y: KanripoDoc) -> None:
        self.x, self.y = x, y
        self.matches: list[Match] = []

    def __repr__(self) -> str:
        return f'Alignment(x="{self.x.id}", y="{self.y.id}")'

    def __str__(self) -> str:
        lines = [f"{self.x.id} <- {self.y.id}"]
        for match in self.matches:
            span = f"{match.start}-{match.end}" if match.found else "—"
            lines.append(f"{match.lemma}\t{span}\t{match.confidence}")
        return "\n".join(lines)

    def align_annotations(self) -> "Alignment":
        # bail out if there's nothing to align from
        if not self.y.meta.get("annotations"):
            return self

        spans = sorted(self.y.meta["annotations"].items())
        lemmas = [self.y.text[start:end] for (start, end), _ in spans]
        self.matches = align_sequence(lemmas, self.x.text)

        layers = self.x.meta.get("layers", [])
        self.x.meta["annotations"] = {}
        self.x.meta["alignment"] = []
        for ((y_start, y_end), annotation), match in zip(spans, self.matches):
            if match.found:
                self.x.meta["annotations"][(match.start, match.end)] = annotation
            self.x.meta["alignment"].append(
                {
                    "lemma": match.lemma,
                    "annotation": annotation,
                    "y_span": (y_start, y_end),
                    "x_span": (match.start, match.end) if match.found else None,
                    "confidence": match.confidence,
                    "layer": layer_at(layers, match.start) if match.found else None,
                }
            )

        return self
