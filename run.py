#!/usr/bin/env python3
from pathlib import Path

import pandas as pd
import tqdm
import typer

from lib.patterns import BLACKLIST, ANNOTATION, FANQIE, YIN, EMPTY_ANNO
from lib.util import clean_text, krp_entity_unicode, split_text, fanqie_to_mc, yin_to_mc, char_to_mc, align_refs


def parse(
    in_dir: Path = Path("src/"),
    out_dir: Path = Path("out/"),
    kr_table_path: Path = Path("data/kr-unicode.tsv"),
    mc_table_path: Path = Path("data/GDR-SBGY-full.tsv"),
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
    unicode_table = pd.read_csv(
        kr_table_path,
        sep="\t",
        names=["form", "unicode"],
    )
    to_unicode = lambda entity: krp_entity_unicode(unicode_table, entity)

    # read baxter's song ben guang yun middle chinese table
    mc_table = pd.read_csv(
        mc_table_path,
        sep="\t",
        names=["char", "fanqie", "initial", "rime", "reading", "group"],
    ).drop_duplicates()
    _fanqie_to_mc = lambda char: fanqie_to_mc(char, mc_table)
    _yin_to_mc = lambda char: yin_to_mc(char, mc_table)
    _char_to_mc = lambda char: char_to_mc(char, mc_table)

    # clean out destination directory
    out_dir.mkdir(exist_ok=True)
    for file in out_dir.glob("*.txt"):
        file.unlink()

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
        text = FANQIE.sub(_fanqie_to_mc, text)

        # convert direct "sounds like" annotations
        text = YIN.sub(_yin_to_mc, text)

        # realign annotations that refer to other characters
        # text = align_refs(text)

        # TODO check for any readings that are invalid per the Guangyun


        # add middle chinese readings for any remaining non-polyphones
        text = EMPTY_ANNO.sub(_char_to_mc, text)

        # save the text into the output folder
        output = out_dir / f"{file.stem}.txt"
        output.open(mode="w").write(text)


if __name__ == "__main__":
    typer.run(parse)

__doc__ = parse.__doc__  # type: ignore
