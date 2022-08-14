from itertools import chain

import typer
from fastcore.transform import Pipeline

from lib.transforms import (
    KanripoUnicode,
    remove_comments,
    remove_page_breaks,
    remove_pilcrows,
    remove_whitespace,
    remove_xml_tags,
)

from lib.loaders import KanripoTxtDataset, KanripoXmlDataset

def main() -> None:
    zhengwen_txt = KanripoTxtDataset("txt/zhengwen")
    zhengwen_xml = KanripoXmlDataset("txt/zhengwen")
    jdsw_txt = KanripoTxtDataset("txt/jdsw")

    txt_pipe = Pipeline(funcs=[
        KanripoUnicode(),
        remove_comments,
        remove_page_breaks,
        remove_pilcrows,
        remove_whitespace,
    ])
    xml_pipe = Pipeline(funcs=[
        remove_xml_tags,
        *txt_pipe,
    ])

    zhengwen = chain(
        (txt_pipe(t) for t in zhengwen_txt),
        (xml_pipe(t) for t in zhengwen_xml),
    )
    jdsw = (txt_pipe(t) for t in jdsw_txt)

    print([t[:15] for t in jdsw])


if __name__ == "__main__":
    typer.run(main)
