import csv
from pathlib import Path
from typing import Iterable

import typer
from fastcore.transform import Pipeline
import jsonlines


from lib.documents import KanripoDoc
from lib.loaders import KanripoTxtDataset
from lib.transforms import (
    KanripoUnicode,
    RemoveComments,
    RemovePageBreaks,
    RemoveChars,
    RemoveWhitespace,
    HealAnnotations,
    ExtractAnnotations,
)


def load_juan_data(juan_path=Path("data/juan.csv")) -> dict[str, dict[str, str]]:
    reader = csv.DictReader(open(juan_path, encoding="utf-8"))
    juan = {"KR1g0003_025": {"zhengwen_id": "KR5c0057", "juan": "1"}}
    for row in reader:
        for doc_id in row["jdsw_id"].split(","):
            juan[doc_id] = {
                "zhengwen_id": row["zhengwen_id"],
            }
    return juan


def process_docs_lazy(
    txt_path=Path("txt/jdsw"), book: str = ""
) -> Iterable[KanripoDoc]:
    path = txt_path / book
    jdsw = KanripoTxtDataset(path)
    pipe = Pipeline(
        funcs=[
            KanripoUnicode,
            RemoveComments,
            RemovePageBreaks,
            RemoveChars("0123456789.．¶*"),
            RemoveWhitespace,
            HealAnnotations,
            ExtractAnnotations,
        ]
    )
    return map(pipe, jdsw)


def write_csv(
    docs: Iterable[KanripoDoc], juan: dict, out_path: str = "annotations.csv"
) -> None:
    with open(out_path, "w", encoding="utf-8") as f:
        fields = ["jdsw_id", "zhengwen_id", "juan", "index", "headword", "annotation"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for doc in docs:
            for i, ((start, end), annotation) in enumerate(
                doc.meta["annotations"].items()
            ):
                writer.writerow(
                    {
                        "jdsw_id": doc.id,
                        "zhengwen_id": juan[doc.id]["zhengwen_id"],
                        "juan": juan[doc.id].get("juan", int(doc.id[-3:])),
                        "index": i + 1,
                        "headword": doc.text[start:end],
                        "annotation": annotation,
                    }
                )


def write_jsonl(
    docs: Iterable[KanripoDoc], juan: dict, out_path: str = "annotations.jsonl"
) -> None:
    with open(out_path, "w", encoding="utf-8") as f:
        writer = jsonlines.Writer(f)
        for doc in docs:
            for i, ((start, end), annotation) in enumerate(
                doc.meta["annotations"].items()
            ):
                writer.write(
                    {
                        "text": annotation,
                        "meta": {
                            "jdsw_id": doc.id,
                            "zhengwen_id": juan[doc.id]["zhengwen_id"],
                            "juan": juan[doc.id].get("juan", int(doc.id[-3:])),
                            "index": i + 1,
                            "headword": doc.text[start:end],
                        },
                    }
                )


def main(fmt: str = "csv", book: str = "") -> None:
    # load the juan data
    juan = load_juan_data()

    # set up processing pipeline
    docs = process_docs_lazy(book=book)

    # write the annotations to a file
    if fmt == "csv":
        write_csv(docs, juan)
    elif fmt == "jsonl" or fmt == "json":
        write_jsonl(docs, juan)


if __name__ == "__main__":
    typer.run(main)
