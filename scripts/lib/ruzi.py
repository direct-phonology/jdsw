"""
Resolve 如字 ("read as the usual graph") glosses to grounded default readings.

When Lu Deming writes 如字 he is declining to assign a special reading: the
character keeps its ordinary (default) Middle Chinese reading rather than one
of the marked readings he gives elsewhere via fanqie. Recovering that default
turns the ~5% of annotations carrying 如字 from discards into labeled
training examples.

The defaults come from a curated profile table, assets/default_reading_profiles.csv,
produced by an elimination analysis outside this module. Each row is one
character; the columns this resolver reads are:

    char                 the character
    ruzi_default         its resolved default reading, or empty if the
                         elimination could not single one out
    ruzi_confidence      confidence in that default, 0.0–1.0
    signals_agree        whether the independent signals (bare-如字 vs.
                         least-marked) agreed

A character with a non-empty ruzi_default resolves to it; an empty default
(the majority — elimination is conservative) is left unresolved. Confidence
and agreement ride along on each record so consumers can filter, mirroring
how polyphone.py emits flagged-but-kept validation verdicts. When the file is
absent the resolver is simply empty and 如字 glosses go unresolved, so the
pipeline still runs.
"""

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

DEFAULT_PROFILE_PATH = Path("assets/default_reading_profiles.csv")

# resolution verdicts
RESOLVED = "resolved"  # the profile gives a single default reading
UNRESOLVED = "unresolved"  # no default (absent, or elimination was inconclusive)


@dataclass
class Profile:
    reading: str  # ruzi_default; "" when the elimination was inconclusive
    confidence: float
    signals_agree: bool


class DefaultReadings:
    """Default (如字) readings per character, loaded from a profile CSV."""

    def __init__(self, table: Optional[dict[str, Profile]] = None) -> None:
        self.table = table or {}

    @classmethod
    def of(cls, readings: dict[str, str]) -> "DefaultReadings":
        """Build from a plain char→reading map (test/programmatic convenience)."""
        return cls({c: Profile(r, 1.0, True) for c, r in readings.items()})

    @classmethod
    def from_csv(cls, path: Path = DEFAULT_PROFILE_PATH) -> "DefaultReadings":
        table: dict[str, Profile] = {}
        if path.exists():
            for row in csv.DictReader(open(path, encoding="utf-8")):
                table[row["char"]] = Profile(
                    reading=row.get("ruzi_default", "").strip(),
                    confidence=float(row.get("ruzi_confidence") or 0.0),
                    signals_agree=row.get("signals_agree", "").strip() == "True",
                )
        return cls(table)

    def resolve(self, char: str) -> tuple[Optional[str], str]:
        """The character's default reading and a verdict (RESOLVED/UNRESOLVED)."""
        profile = self.table.get(char)
        if profile and profile.reading:
            return profile.reading, RESOLVED
        return None, UNRESOLVED

    def confidence(self, char: str) -> float:
        profile = self.table.get(char)
        return profile.confidence if profile else 0.0

    def signals_agree(self, char: str) -> bool:
        profile = self.table.get(char)
        return bool(profile and profile.signals_agree)
