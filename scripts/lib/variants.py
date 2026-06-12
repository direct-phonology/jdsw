import json
from functools import lru_cache
from pathlib import Path

NORMALIZATION_PATH = Path("assets/normalization.json")
VARIANTS_PATH = Path("assets/variants.json")


def load_table(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def variant_table() -> dict[int, str]:
    """
    Combined character-equivalence table for use with str.translate().

    Composes two layers, applied as a single mapping:
    - normalization.json: mechanical Unicode equivalences (compatibility forms,
      width/punctuation folding) that carry no philological judgment
    - variants.json: curated graphic variant (異體字) pairs

    Variant entries are keyed on normalized forms, so normalization is applied
    first and the variant mapping second.
    """
    normalization = load_table(NORMALIZATION_PATH)
    variants = load_table(VARIANTS_PATH)

    combined = {k: variants.get(v, v) for k, v in normalization.items()}
    for k, v in variants.items():
        combined.setdefault(k, v)

    return str.maketrans(combined)


def normalize(text: str) -> str:
    """Map all variant characters in a text to their canonical forms."""
    return text.translate(variant_table())
