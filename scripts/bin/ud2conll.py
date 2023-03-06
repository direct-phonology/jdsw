"""
Convert the Kyoto Universal Dependency Treebank from CoNLL-U to CoNLL-2000 format.
"""

import sys
import typer
from pathlib import Path
from spacy.morphology import Morphology

GLOSS_ENT_MAP = {
    "[surname]": "SURNAME",
    "[given-name]": "GIVEN_NAME",
    "[country-name]": "COUNTRY",
    "[place-name]": "PLACE",
    "[book-name]": "BOOK",
    "[era-name]": "ERA",
    # ignored; only one instance each
    # "[poetry-name]": "POETRY",
    # "[sword-name]": "WEAPON",
}

NAME_TYPE_ENT_MAP = {
    "Sur": "SURNAME",
    "Giv": "GIVEN_NAME",
    "Prs": "COURTESY_NAME",
    "Nat": "COUNTRY",
    "Geo": "PLACE",
}

ENT_GLOSSES = set(GLOSS_ENT_MAP.keys())
ENT_NAME_TYPES = set(NAME_TYPE_ENT_MAP.keys())
ENT_TYPES = set(GLOSS_ENT_MAP.values()) | set(NAME_TYPE_ENT_MAP.values())

def main(file: Path) -> None:
    contents = file.read_text(encoding="utf-8").strip()
    sentences = contents.split("\n\n")

    for sentence in sentences:
        output = []
        lines = sentence.strip().split("\n")
        while lines[0].startswith("#"):
            output.append(f"{lines.pop(0)}\n")
        for line in lines:
            id_, word, lemma, pos, tag, morph, head, dep, _1, misc = line.split("\t")
            name_type = Morphology.feats_to_dict(morph).get("NameType")
            gloss = Morphology.feats_to_dict(misc).get("Gloss", "")
            ent_type = None

            if gloss.endswith("name]"):
                ent_type = GLOSS_ENT_MAP.get(gloss)
            elif name_type:
                ent_type = NAME_TYPE_ENT_MAP.get(name_type)
            
            if ent_type:
                if len(word) == 1:
                    output.append(f"{word} B-{ent_type}\n")
                else:
                    output.append(f"{word[0]} B-{ent_type}\n")
                    for char in word[1:]:
                        output.append(f"{char} I-{ent_type}\n")
            else:
                if len(word) == 1:
                    output.append(f"{word} O\n")
                else:
                    output.append(f"{word[0]} O\n")
                    for char in word[1:]:
                        output.append(f"{char} O\n")

        sys.stdout.writelines(output)
        sys.stdout.write("\n")

if __name__ == "__main__":
    typer.run(main)
