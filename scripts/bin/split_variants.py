#!/usr/bin/env python3

import json
import re
import unicodedata
from pathlib import Path
from typing import Optional

import typer


def is_mechanical(source: str, target: str) -> bool:
    """
    True if a mapping is derivable from Unicode alone: compatibility
    normalization (NFKC) or folding to an ASCII equivalent (fullwidth forms,
    CJK punctuation). Everything else is a philological judgment.
    """
    if unicodedata.normalize("NFKC", source) == target:
        return True
    if target.isascii() and not source.isascii():
        return True
    return False


def main(
    variants_file: Path = Path("assets/variants.json"),
    normalization_file: Path = Path("assets/normalization.json"),
    unihan_file: Optional[Path] = typer.Option(
        None, help="Unihan_Variants.txt, to report kSemanticVariant corroboration"
    ),
) -> None:
    """
    Split the character equivalency table into two layers.

    The variants table mixes mechanical Unicode normalization (compatibility
    forms, width/punctuation folding) with curated graphic variant (異體字)
    pairs. This script separates them: mechanical mappings move to the
    normalization table, philological pairs stay in the variants table.
    Both are consumed together via scripts.lib.variants.variant_table().
    """
    table = json.loads(variants_file.read_text(encoding="utf-8"))

    normalization, variants = {}, {}
    for source, target in table.items():
        if is_mechanical(source, target):
            normalization[source] = target
        else:
            variants[source] = target

    # if Unihan data is available, report which curated pairs it corroborates
    if unihan_file is not None:
        semvar = re.compile(r"U\+(\w+)\tkSemanticVariant\t(.+)")
        corroborated = set()
        for line in unihan_file.read_text(encoding="utf-8").splitlines():
            if match := semvar.match(line):
                char = chr(int(match.group(1), 16))
                targets = [chr(int(c, 16)) for c in re.findall(r"U\+(\w+)", match.group(2))]
                for target in targets:
                    if variants.get(char) == target or variants.get(target) == char:
                        corroborated.add((char, target))
        typer.echo(
            f"{len(corroborated)}/{len(variants)} variant pairs corroborated "
            "by kSemanticVariant",
            err=True,
        )

    normalization_file.write_text(
        json.dumps(normalization, ensure_ascii=False, indent=1, sort_keys=True),
        encoding="utf-8",
    )
    variants_file.write_text(
        json.dumps(variants, ensure_ascii=False, indent=1, sort_keys=True),
        encoding="utf-8",
    )
    typer.echo(
        f"{len(normalization)} normalization mappings, {len(variants)} variant pairs",
        err=True,
    )


if __name__ == "__main__":
    typer.run(main)

__doc__ = main.__doc__  # type: ignore
