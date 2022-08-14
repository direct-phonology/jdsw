from itertools import chain

import typer
from fastcore.transform import Pipeline

from lib.transforms import (
    KanripoUnicode,
    KanripoTeiXml,
    remove_comments,
    remove_page_breaks,
    remove_pilcrows,
    remove_whitespace,
)

from lib.loaders import KanripoDataset

def main() -> None:
    zhengwen_txt = KanripoDataset("txt/zhengwen")
    zhengwen_xml = KanripoDataset("txt/zhengwen", ext="xml")

    txt_pipe = Pipeline(funcs=[
        KanripoUnicode(),
        remove_comments,
        remove_page_breaks,
        remove_pilcrows,
        remove_whitespace,
    ])
    xml_pipe = Pipeline(funcs=[KanripoTeiXml(), *txt_pipe])

    zhengwen = chain(
        (txt_pipe(t) for t in zhengwen_txt),
        (xml_pipe(t) for t in zhengwen_xml),
    )

    print([t[:15] for t in zhengwen])


if __name__ == "__main__":
    typer.run(main)
