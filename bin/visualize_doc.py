from itertools import chain
import csv

import typer
from fastcore.transform import Pipeline
from lib.alignment import Alignment
from lib.documents import KanripoDoc, merge_docs
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


def main(doc_id: str) -> None:
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

    # preprocess all documents through the pipeline
    zhengwen_docs = map(text_pipe, chain(zhengwen_txt, zhengwen_xml))
    jdsw_docs = map(text_pipe, jdsw_txt)
    all_docs = {doc.id: doc for doc in chain(zhengwen_docs, jdsw_docs)}
    alignments = []

    # laozi: combine all zhengwen juan into one doc and align with jdsw
    zw_laozi_docs = [doc for id, doc in all_docs.items() if id.startswith("KR5c0057")]
    zw_laozi = merge_docs(*zw_laozi_docs, meta={"title": "老子"})
    jdsw_laozi = anno_pipe(all_docs["KR1g0003_025"])
    jdsw_laozi.meta["title"] = "老子"
    alignments.append(Alignment(zw_laozi, jdsw_laozi))

    # everything else: use juan.csv to align; join jdsw juan into one doc if multiple
    reader = csv.DictReader(open("data/juan.csv", encoding="utf-8"))
    for row in reader:
        # get the relevant zhengwen doc
        zw_doc = all_docs[row["zhengwen_id"]]

        # combine multiple jdsw juan into one doc, if necessary, and extract annotations
        jdsw_ids = row["jdsw_id"].split(",")
        jdsw_doc = merge_docs(*[all_docs[jdsw_id] for jdsw_id in jdsw_ids])
        jdsw_doc = anno_pipe(jdsw_doc)

        # generate a title by composing the text title with the juan title
        title = f"{row['doc_title']}《{row['juan_title']}》"
        zw_doc.meta["title"] = title
        jdsw_doc.meta["title"] = title

        # align the two docs
        alignments.append(Alignment(zw_doc, jdsw_doc))

    # use the alignments to transfer annotations
    for alignment in alignments:
        alignment.align_annotations()

    # visualize the desired doc
    the_doc = next(alm for alm in alignments if alm.y.id == doc_id).y
    from lib.visualizers import serve

    serve(the_doc, page=True, options={
        "rtl": False,
        "columnar_annotations": False
    })


if __name__ == "__main__":
    typer.run(main)
