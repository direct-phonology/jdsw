from typing import Any, Iterable, Dict, Optional
from pathlib import Path

from spacy.util import minify_html

from lib.documents import KanripoDoc

_html = {}
_css = (Path(__file__).parent / "style.css").read_text(encoding="utf-8")


def render(
    docs: Iterable[KanripoDoc] | KanripoDoc,
    style: str = "anno",
    page: bool = False,
    minify: bool = False,
    options: Dict[str, Any] = {},
) -> str:
    factories = {"anno": AnnotationRenderer}
    if style not in factories:
        raise ValueError(f"Unknown euphoNy style: {style}.")
    if isinstance(docs, KanripoDoc):
        docs = [docs]
    renderer = factories[style](options)
    _html["parsed"] = renderer.render(docs, page=page, minify=minify).strip()
    html = _html["parsed"]
    return html


def serve(
    docs: Iterable[KanripoDoc] | KanripoDoc,
    style: str = "anno",
    page: bool = False,
    minify: bool = False,
    options: Dict[str, Any] = {},
    port: int = 8000,
    host: str = "0.0.0.0",
) -> None:
    from wsgiref import simple_server

    render(docs, style=style, page=page, minify=minify, options=options)
    with simple_server.make_server(host, port, app) as httpd:
        print(f"Using the '{style}' visualizer.")
        print(f"Starting server on http://{host}:{port}...")
        httpd.serve_forever()


def app(environ, start_response):
    headers = [("Content-type", "text/html; charset=utf-8")]
    start_response("200 OK", headers)
    res = _html["parsed"].encode(encoding="utf-8")
    return [res]


class AnnotationRenderer:
    """Render a Doc with its associated annotations as HTML."""

    style = "anno"

    def __init__(self, options: Dict[str, Any] = {}) -> None:
        pass

    def render(
        self, docs: Iterable[KanripoDoc], page: bool = False, minify: bool = False
    ) -> str:
        rendered = [
            self.render_doc(
                doc.text, doc.meta.get("annotations", {}), doc.meta.get("title", "")
            )
            for doc in docs
        ]
        if page:
            markup = TPL_PAGE.format(style=_css, content="".join(rendered))
        else:
            markup = "".join(rendered)
        if minify:
            return minify_html(markup)
        return markup

    def render_doc(
        self, text: str, annotations: Dict[int, str], title: Optional[str]
    ) -> str:
        output = ""
        for i, char in enumerate(text):
            output += TPL_CHAR.format(content=char, cls="")
            if i in annotations:
                output += self.render_annotation(annotations[i])
        return TPL_DOC.format(content=output, title=title)

    def render_annotation(self, annotation: str) -> str:
        middle = len(annotation) // 2 + (len(annotation) % 2)
        right, left = annotation[:middle], annotation[middle:]
        fmt_right = "".join([TPL_CHAR.format(content=char) for char in right])
        fmt_left = "".join([TPL_CHAR.format(content=char) for char in left])
        return TPL_ANNOTATION.format(right=fmt_right, left=fmt_left)


TPL_PAGE = """
<!DOCTYPE html>
<html lang="zh">
  <head>
    <meta charset="utf-8" />
    <title>euphoNy</title>
    <style>{style}</style>
  </head>
  <body>{content}</body>
</html>
""".strip()

TPL_DOC = """
<article class="doc">
  <h1>{title}</h1>
  <p>{content}</p>
</article>
""".strip()

TPL_ANNOTATION = """
<span class="anno">
    <span class="col">{right}</span>
    <span class="col">{left}</span>
</span>
""".strip()

TPL_CHAR = """
<span class="char">{content}</span>
""".strip()
