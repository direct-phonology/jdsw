from itertools import chain
import csv

import typer
from fastcore.transform import Pipeline
from lib.alignment import Alignment
from lib.documents import KanripoDoc
from lib.loaders import KanripoTxtDataset, KanripoXmlDataset
from lib.transforms import (
    KanripoUnicode,
    RemoveComments,
    RemovePageBreaks,
    RemoveChars,
    RemoveWhitespace,
    HealAnnotations,
    ExtractAnnotations,
)


def main() -> None:
    zhengwen_txt = KanripoTxtDataset("txt/zhengwen")
    zhengwen_xml = KanripoXmlDataset("txt/zhengwen")
    jdsw_txt = KanripoTxtDataset("txt/jdsw")

    text_pipe = Pipeline(
        funcs=[
            KanripoUnicode,
            RemoveComments,
            RemovePageBreaks,
            RemoveChars("0123456789.．¶*"),
            RemoveWhitespace,
        ]
    )
    anno_pipe = Pipeline(
        funcs=[
            HealAnnotations,
            ExtractAnnotations,
        ]
    )

    zhengwen_docs = map(text_pipe, chain(zhengwen_txt, zhengwen_xml))
    jdsw_docs = map(text_pipe, jdsw_txt)
    all_docs = {doc.id: doc for doc in chain(zhengwen_docs, jdsw_docs)}
    align_map: dict[KanripoDoc, KanripoDoc] = {}

    # laozi: combine all zhengwen juan into one doc and align with jdsw
    zw_laozi_text = [doc for doc in all_docs.values() if doc.id.startswith("KR5c0057")]
    zhengwen_laozi = KanripoDoc(
        id="KR5c0057",
        text="".join([doc.text for doc in sorted(zw_laozi_text)]),
    )
    align_map[zhengwen_laozi] = all_docs["KR1g0003_025"]

    # everything else: use juan.csv to align; join jdsw juan into one doc if multiple
    reader = csv.DictReader(open("data/juan.csv", encoding="utf-8"))
    for row in reader:
        jdsw_juan = [all_docs[doc_id] for doc_id in row["jdsw_id"].split(",")]
        align_map[all_docs[row["zhengwen_id"]]] = KanripoDoc(
            id=row["jdsw_id"],
            text="".join([doc.text for doc in jdsw_juan]),
        )

    # run the annotation pipe on the joined versions so annotation indices are correct
    for zhengwen_doc, jdsw_doc in align_map.items():
        align_map[zhengwen_doc] = anno_pipe(jdsw_doc)

    # align the zhengwen and jdsw versions
    alignments = [Alignment(zhengwen, jdsw) for zhengwen, jdsw in align_map.items()]
    for alignment in alignments[:5]:
        print(alignment)

    # transfer the annotations using the aligment


if __name__ == "__main__":
    typer.run(main)
