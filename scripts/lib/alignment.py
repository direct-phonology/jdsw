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

import re
from bisect import bisect_right
from dataclasses import dataclass
from itertools import groupby
from typing import Optional

from scripts.lib.documents import KanripoDoc
from scripts.lib.variants import normalize

# alignment confidence levels, from best to worst
ANCHOR = "anchor"  # exact match selected by weighted LIS
GAP = "gap"  # exact match found between two anchors
ALTERNATE = "alternate"  # matched via an alternative graph cited in the gloss
PARTIAL = "partial"  # prefix/suffix match found between two anchors
UNMATCHED = "unmatched"  # no plausible position found

# placeholder for a damaged/illegible character in SBCK transcriptions;
# treated as a wildcard that matches any lemma character
DAMAGED = "⬤"

# glosses citing alternative graphs for a character of the headword,
# e.g. 本又作X, 本亦作X, 一本作X, including chains like 本又作X又作Y
ALTERNATE_GRAPH = re.compile(r"本[又亦或]?作(.(?:又作.)*)")
ALTERNATE_CHAIN = re.compile(r"又作(.)")


@dataclass
class Match:
    """The aligned position of a single lemma in the source text."""

    index: int  # position of the lemma in the input sequence
    lemma: str
    start: Optional[int]  # span in the source text, if found
    end: Optional[int]
    confidence: str
    # end of the portion of the span actually verified against the text; for
    # partial matches the rest of the span is extrapolated from lemma length
    verified_end: Optional[int] = None

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


def _wildcard_find(needle: str, haystack: str, start: int = 0) -> int:
    """
    Like str.find, but a DAMAGED placeholder in the haystack matches any
    needle character. Falls back to str.find when no placeholder is present.
    """
    if DAMAGED not in haystack:
        return haystack.find(needle, start)
    for i in range(start, len(haystack) - len(needle) + 1):
        if all(h == n or h == DAMAGED for h, n in zip(haystack[i:], needle)):
            return i
    return -1


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
    lemma: str,
    text: str,
    window_start: int,
    window_end: int,
    alternates: tuple = (),
) -> Optional[Match]:
    """Place a non-anchor lemma within the window between its flanking anchors."""
    window = text[window_start:window_end]

    # exact match within the window (damaged characters match anything)
    pos = _wildcard_find(lemma, window)
    if pos != -1:
        start = window_start + pos
        return Match(-1, lemma, start, start + len(lemma), GAP)

    # retry with alternative graphs cited in the gloss (本又作X), substituted
    # for each character of the lemma in turn
    for alt in alternates:
        for i in range(len(lemma)):
            variant = lemma[:i] + alt + lemma[i + 1 :]
            pos = _wildcard_find(variant, window)
            if pos != -1:
                start = window_start + pos
                return Match(-1, lemma, start, start + len(lemma), ALTERNATE)

    # longest prefix or suffix match, extended to the full lemma length;
    # lemmas of 3+ characters must verify at least 2, so that a partial can't
    # anchor a long lemma on a single common character
    min_length = 2 if len(lemma) >= 3 else 1
    for length in range(len(lemma) - 1, min_length - 1, -1):
        pos = _wildcard_find(lemma[:length], window)
        if pos != -1:
            start = window_start + pos
            end = min(start + len(lemma), window_end)
            return Match(-1, lemma, start, end, PARTIAL, verified_end=start + length)
        pos = _wildcard_find(lemma[-length:], window)
        if pos != -1:
            end = window_start + pos + length
            start = max(end - len(lemma), window_start)
            return Match(-1, lemma, start, end, PARTIAL, verified_end=end)

    return None


def alternate_graphs(annotation: str) -> tuple:
    """Alternative graphs for the headword cited in an annotation (本又作X)."""
    graphs = []
    for segment in ALTERNATE_GRAPH.findall(annotation):
        graphs.append(segment[0])
        graphs.extend(ALTERNATE_CHAIN.findall(segment[1:]))
    return tuple(graphs)


def align_sequence(
    lemmas: list[str],
    text: str,
    max_candidates: int = 128,
    alternates: Optional[list[tuple]] = None,
) -> list[Match]:
    """
    Align an ordered sequence of lemmata against a text, returning one Match
    per lemma. Lemmata occurring more than max_candidates times are excluded
    from anchor selection and placed by gap-filling only. If alternates are
    given (per-lemma graphs cited in the annotation, see alternate_graphs),
    they are substituted into the lemma when gap-filling finds no direct match.
    """
    text_norm = normalize(text)
    lemmas_norm = [normalize(lemma) for lemma in lemmas]
    alternates_norm = [
        tuple(normalize(a) for a in alts)
        for alts in (alternates or [()] * len(lemmas))
    ]

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

        match = _fill_gap(lemma, text_norm, cursor, window_end, alternates_norm[i])
        if match:
            match.index, match.lemma = i, lemmas[i]
            matches.append(match)
            # a partial's unverified tail must not consume window space the
            # next lemma may legitimately occupy
            cursor = match.verified_end if match.verified_end is not None else match.end
        else:
            matches.append(Match(i, lemmas[i], None, None, UNMATCHED))

    return matches


def layer_at(layers: list, position: int) -> str:
    """
    Edition layer ("main", "commentary", "unknown") containing a text
    position. Falls back to "unknown" rather than "main": a position with no
    layer span is one we have no layer evidence for, and silently calling it
    "main" mislabels witnesses whose layers were never determined.
    """
    for start, end, label in layers:
        if start <= position < end:
            return label
    return "unknown"


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
        alternates = [alternate_graphs(str(annotation)) for _, annotation in spans]
        self.matches = align_sequence(lemmas, self.x.text, alternates=alternates)

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
