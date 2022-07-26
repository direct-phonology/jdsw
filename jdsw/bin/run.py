#!/usr/bin/env python3
import json
from pathlib import Path
from typing import Any, Counter

import pandas as pd
import tqdm
import typer

from lib.patterns import BLACKLIST
from lib.phonology import Reconstruction
from lib.util import (
    align_refs,
    augment_annotations,
    clean_text,
    convert_fanqie,
    convert_yin,
    krp_entity_unicode,
    split_text,
)


def parse(
    in_dir: Path = Path("src/"),
    out_dir: Path = Path("out/"),
    kr_table_path: Path = Path("data/kr-unicode.csv"),
    mc_table_path: Path = Path("data/GDR-SBGY-full.csv"),
) -> None:
    """
    Convert the Jingdian Shiwen into a .conll-like annotated text format.

    All files in the input folder are processed and split into original text
    and annotations. The text is reformatted to list one annotation per line
    with the character it immediately follows, and then new files are saved in
    the output folder.

    Combination characters and other special entities from Kanseki Repository
    text are converted to unicode placeholders, and all other textual artifacts
    (punctuation, whitespace, line breaks, etc.) are removed.
    """

    # read unicode conversion table
    unicode_table = pd.read_csv(kr_table_path)
    to_unicode = lambda entity: krp_entity_unicode(unicode_table, entity)

    # read gian's guangyun middle chinese reconstruction
    mc_table = pd.read_csv(mc_table_path)
    rc = Reconstruction(mc_table)

    # clean out destination directory
    out_dir.mkdir(exist_ok=True)
    for file in out_dir.glob("*.txt"):
        file.unlink()

    # track statistics
    stats: dict[str, Any] = {
        "errors": Counter(),
    }

    # process source text
    typer.echo("Creating annotated text...")
    for file in tqdm.tqdm(sorted(list(in_dir.glob("*.txt")))):

        # ignore blacklisted material
        if any([file.stem in name for name in BLACKLIST]):
            continue

        # read the file and clean it
        text = clean_text(file.read_text(), to_unicode)

        # reformat conll-style
        text = split_text(text)

        # read the file and strip annotations we can't convert
        # text = ANNOTATION.sub(filter_annotation, text)

        # convert fanqie annotations
        text = convert_fanqie(text, rc, stats)

        # convert direct "sounds like" annotations
        text = convert_yin(text, rc, stats)

        # realign annotations that refer to other characters
        text = align_refs(text, rc)

        # add middle chinese readings for any remaining non-polyphones
        text = augment_annotations(text, rc, stats)

        # save the text into the output folder
        output = out_dir / f"{file.stem}.txt"
        output.open(mode="w").write(text)

    # write out statistics
    typer.echo("Writing statistics...")
    with open(out_dir / "stats.json", "w", encoding="utf8") as f:
        f.write(json.dumps(dict(stats), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    typer.run(parse)

__doc__ = parse.__doc__  # type: ignore
