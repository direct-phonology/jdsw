import re

from unittest import TestCase

from lib.documents import KanripoDoc
from lib.visualizers import AnnotationRenderer


def split_html(html: str) -> list[str]:
    return re.sub(r">\s+<", "><", html.strip()).replace("><", ">\n<").split("\n")


class TestAnnotationRenderer(TestCase):
    def test_render_annotations(self):
        """should render annotations interleaved with text"""
        self.maxDiff = None
        doc = KanripoDoc(
            id="doc",
            text="abcdefghi",
            meta={"title": "doc", "annotations": {(0, 3): "one", (4, 6): "two"}},
        )
        renderer = AnnotationRenderer()
        self.assertEqual(
            split_html(renderer.render([doc], page=False)),
            split_html(
                """
            <article class="doc">
                <h1>doc</h1>
                <p>
                    <span class="char">a</span>
                    <span class="char">b</span>
                    <span class="char">c</span>
                    <span class="anno">
                        <span class="char">o</span>
                        <span class="char">n</span>
                        <span class="char">e</span>
                    </span>
                    <span class="char">d</span>
                    <span class="char">e</span>
                    <span class="char">f</span>
                    <span class="anno">
                        <span class="char">t</span>
                        <span class="char">w</span>
                        <span class="char">o</span>
                    </span>
                    <span class="char">g</span>
                    <span class="char">h</span>
                    <span class="char">i</span>
                </p>
            </article>
        """
            ),
        )
