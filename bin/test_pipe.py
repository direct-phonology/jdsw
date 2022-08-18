from itertools import chain

import typer
from fastcore.transform import Pipeline
from lib.loaders import KanripoTxtDataset, KanripoXmlDataset
from lib.transforms import (
    KanripoUnicode,
    RemoveComments,
    RemovePageBreaks,
    RemoveChars,
    RemoveWhitespace,
    HealAnnotations,
    ExtractAnnotations
)
from lib.documents import Alignment


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
            *text_pipe,
            HealAnnotations,
            ExtractAnnotations
        ]
    )

    zhengwen = chain(
        (text_pipe(doc) for doc in zhengwen_txt),
        (text_pipe(doc) for doc in zhengwen_xml),
    )
    jdsw = (anno_pipe(t) for t in jdsw_txt)

    out = list(jdsw)
    print(out)



if __name__ == "__main__":
    typer.run(main)
