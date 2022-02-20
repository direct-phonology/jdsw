#!/usr/bin/env python3

import re
from pathlib import Path
from collections import Counter
from typing import cast

import pandas as pd
import typer
from tqdm import tqdm

# fmt: off
ANNOTATION = re.compile(r"""
    ^
    (?P<char>.)             # character being annotated
    \t
    (?P<anno>[^_]+?)        # annotation
    $
""", re.VERBOSE | re.MULTILINE)

FANQIE = re.compile(r"""
    ^
    (?P<char>.)             # character being annotated
    \t
    (?P<initial>[^_])       # initial/onset
    (?P<rime>[^_])          # rime/tone
    反
    $
""", re.VERBOSE | re.MULTILINE)

DIRECT = re.compile(r"""
    ^
    (?P<char>.)             # character being annotated
    \t
    音
    (?P<anno>[^_])          # sounds "the same as" this character
    $
""", re.VERBOSE | re.MULTILINE)

MULTI_FANQIE = re.compile(r"""
    ^
    (?P<char>.)             # character being annotated
    \t
    (?P<initial>[^_])       # initial/onset
    (?P<rime>[^_])          # rime/tone
    反下同
    $
""", re.VERBOSE | re.MULTILINE)
# fmt: on

# case where there's no annotation yet
EMPTY_ANNO = re.compile(r"^(?P<char>.)\t_$", re.MULTILINE)

# types of annotations we care about
WHITELIST = (FANQIE, DIRECT, MULTI_FANQIE)

# track statistics for analysis
STATS = {
    "total": 0,
    "annotated_total": 0,
    "missing_total": 0,
    "initially_empty": 0,
    "all_below": 0,
    "no_reading": Counter(),
    "polyphonic": Counter(),
}


def filter_annotation(annotation: re.Match) -> str:
    """Filter out annotations that we can't convert into readings."""

    # if the annotation isn't in the whitelist, turn it into a _ (blank)
    if not any(annotype.match(annotation.group(0)) for annotype in WHITELIST):
        return f"{annotation.group('char')}\t_"

    return annotation.group(0)


def fanqie_to_mc(annotation: re.Match, mc_table: pd.DataFrame) -> str:
    """Convert a fanqie annotation into a Middle Chinese reading."""
    STATS["total"] += 1  # type: ignore

    # fanqie annotation: fetch initial and rime, combine, then choose the
    # reading for the annotated character that matches the combination
    initial = mc_table[mc_table["zi"] == annotation.group("initial")]
    rime = mc_table[mc_table["zi"] == annotation.group("rime")]

    if initial.empty:
        STATS["missing_total"] += 1  # type: ignore
        STATS["no_reading"][annotation.group("initial")] += 1  # type: ignore
        return f"{annotation.group('char')}\t_"

    if rime.empty:
        STATS["missing_total"] += 1  # type: ignore
        STATS["no_reading"][annotation.group("rime")] += 1  # type: ignore
        return f"{annotation.group('char')}\t_"

    reading = "".join((initial["MCInitial"].iloc[0], rime["MCfinal"].iloc[0])).replace(
        "-", ""
    )

    STATS["annotated_total"] += 1  # type: ignore

    return f"{annotation.group('char')}\t{reading}"


def direct_to_mc(annotation: re.Match, mc_table: pd.DataFrame) -> str:
    """Convert a 'sounds like' annotation into a Middle Chinese reading."""
    STATS["total"] += 1  # type: ignore

    # direct "sounds like" annotation: fetch the reading directly, then choose
    # the reading for the annotated character that matches it
    match = mc_table[mc_table["zi"] == annotation.group("anno")]

    if match.empty:
        STATS["missing_total"] += 1  # type: ignore
        STATS["no_reading"][annotation.group("anno")] += 1  # type: ignore
        return f"{annotation.group('char')}\t_"

    if len(match) > 1:
        STATS["missing_total"] += 1  # type: ignore
        STATS["polyphonic"][annotation.group("anno")] += 1  # type: ignore
        return f"{annotation.group('char')}\t_"

    reading = match["MC"].iloc[0]

    STATS["annotated_total"] += 1  # type: ignore

    return f"{annotation.group('char')}\t{reading}"


def missing_to_mc(annotation: re.Match, mc_table: pd.DataFrame) -> str:
    """Add Middle Chinese readings for un-annotated characters."""
    STATS["total"] += 1  # type: ignore
    STATS["initially_empty"] += 1  # type: ignore

    # empty annotations: see if the character is monophonic, and if so, just
    # use the reading for that character
    match = mc_table[mc_table["zi"] == annotation.group("char")]

    if match.empty:
        STATS["missing_total"] += 1  # type: ignore
        STATS["no_reading"][annotation.group("char")] += 1  # type: ignore
        return f"{annotation.group('char')}\t_"

    if len(match) > 1:
        STATS["missing_total"] += 1  # type: ignore
        STATS["polyphonic"][annotation.group("char")] += 1  # type: ignore
        return f"{annotation.group('char')}\t_"

    reading = match["MC"].iloc[0]

    STATS["annotated_total"] += 1  # type: ignore

    return f"{annotation.group('char')}\t{reading}"


def multi_fanqie_to_mc(txt: str, mc_table: pd.DataFrame) -> str:
    """Convert all multi-fanqie annotations in a text to readings."""

    # split the text into annotations
    annotations = [line.split("\t") for line in txt.splitlines()]

    # get all of the "all below" multi-annotations
    all_below = {line: anno for line, anno in enumerate(annotations) if MULTI_FANQIE.match(f"{anno[0]}\t{anno[1]}")}

    for start_line, annotation in all_below.items():
        char = annotation[0]
        initial = mc_table[mc_table["zi"] == annotation[1][0]]
        rime = mc_table[mc_table["zi"] == annotation[1][1]]

        if initial.empty or rime.empty:
            continue

        reading = "".join(
            (
                initial["MCInitial"].iloc[0],
                rime["MCfinal"].iloc[0],
            )
        ).replace("-", "")

        empty_following = [line for line, anno in enumerate(annotations[start_line + 1:]) if anno[0] == char and anno[1] == "_"]

        for line in empty_following:
            annotations[line][1] = reading
            STATS["annotated_total"] += 1  # type: ignore
            STATS["all_below"] += 1  # type: ignore

        annotations[start_line][1] = reading
        STATS["annotated_total"] += 1  # type: ignore

    # join the annotations back together
    return "\n".join(["\t".join(anno) for anno in annotations])


def mc_to_oc(char: re.Match, oc_table: pd.DataFrame) -> str:
    """Convert a Middle Chinese reading into an Old Chinese reading."""
    return char.group(0)


def annotate(
    in_dir: Path, mc_dir: Path, oc_dir: Path, mc_table_path: Path, oc_table_path: Path
) -> None:
    """Convert the Jingdian Shiwen annotations into Old Chinese readings."""

    # read baxter's song ben guang yun middle chinese table
    mc_table = pd.read_excel(
        mc_table_path, usecols=["zi", "MC", "MCInitial", "MCfinal"]
    ).drop_duplicates()
    _fanqie_to_mc = lambda char: fanqie_to_mc(char, mc_table)
    _direct_to_mc = lambda char: direct_to_mc(char, mc_table)
    _missing_to_mc = lambda char: missing_to_mc(char, mc_table)
    _multi_fanqie_to_mc = lambda txt: multi_fanqie_to_mc(txt, mc_table)

    # read baxter & sagart's old chinese table
    oc_table = pd.read_excel(
        oc_table_path, usecols=["zi", "MC", "OC"]
    ).drop_duplicates()
    _mc_to_oc = lambda char: mc_to_oc(char, oc_table)

    # clean out destination directories
    for loc in [mc_dir, oc_dir]:
        loc.mkdir(exist_ok=True)
        for file in loc.glob("*.txt"):
            file.unlink()

    # add middle chinese readings for as many characters as possible
    typer.echo("Processing middle chinese annotations...")
    for file in tqdm(sorted(list(in_dir.glob("*.txt")))):

        # read the file and strip annotations we can't convert
        text = ANNOTATION.sub(filter_annotation, file.read_text())

        # convert "below all the same" multi-annotations
        text = _multi_fanqie_to_mc(text)

        # convert fanqie annotations
        text = FANQIE.sub(_fanqie_to_mc, text)

        # convert direct "sounds like" annotations
        text = DIRECT.sub(_direct_to_mc, text)

        # add middle chinese readings for any remaining non-polyphones
        text = EMPTY_ANNO.sub(_missing_to_mc, text)

        # save the text into the output folder
        output = mc_dir / f"{file.stem}.txt"
        output.open(mode="w").write(text)

    # print statistics
    typer.echo("\nStatistics:")
    typer.echo(f"  {STATS['total']} total characters")
    typer.echo(f"  {STATS['initially_empty']} characters initially empty")
    typer.echo(f"  {STATS['annotated_total']} annotated characters")
    typer.echo(f"  {STATS['missing_total']} unannotated characters")
    typer.echo(f"  {STATS['all_below']} characters from multi-annos")
    typer.echo(f"  {STATS['polyphonic'].total()} polyphonic characters")  # type: ignore
    typer.echo(f"  Top 5:\t\t{STATS['polyphonic'].most_common(5)}")  # type: ignore
    typer.echo(f"  {STATS['no_reading'].total()} characters with no reading")  # type: ignore
    typer.echo(f"  Top 5:\t\t{STATS['no_reading'].most_common(5)}")  # type: ignore

    # write out statistics
    polyphone_stats = Path("polyphones.txt")
    polyphone_stats.open(mode="w").write(
        "\n".join(
            [
                "\t".join([entry[0], str(entry[1])])
                for entry in STATS["polyphonic"].most_common(100)  # type: ignore
            ]
        )
    )
    no_reading_stats = Path("no_reading.txt")
    no_reading_stats.open(mode="w").write(
        "\n".join(
            [
                "\t".join([entry[0], str(entry[1])])
                for entry in STATS["no_reading"].most_common(100)  # type: ignore
            ]
        )
    )


if __name__ == "__main__":
    typer.run(annotate)

__doc__ = annotate.__doc__  # type: ignore
