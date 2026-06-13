"""
merge_docs must preserve per-part layer spans under per-work alignment: a
work's fascicles are merged into one text before aligning, and the layer-aware
reading extraction (注同 scope, layer_at) depends on the merged doc carrying
correctly-offset layers. A regression that drops or mis-offsets them silently
disables that extraction for every multi-fascicle work.
"""

from unittest import TestCase

from scripts.lib.documents import KanripoDoc, merge_docs


class TestMergeDocsLayers(TestCase):
    def test_layers_survive_two_doc_merge_with_offsets(self) -> None:
        a = KanripoDoc(
            id="KR0001_001",
            text="經經注",  # 2 main, 1 commentary
            meta={
                "layers": [(0, 2, "main"), (2, 3, "commentary")],
                "jdsw_self": [(2, "音義")],
            },
        )
        b = KanripoDoc(
            id="KR0001_002",
            text="注經",  # 1 commentary, 1 main
            meta={
                "layers": [(0, 1, "commentary"), (1, 2, "main")],
                "jdsw_self": [(0, "曰")],
            },
        )
        merged = merge_docs(a, b)

        self.assertEqual(merged.text, "經經注注經")
        # b's spans are offset by len(a) == 3; a's trailing commentary (…2-3)
        # abuts b's leading commentary (now 3-4) across the join and coalesces
        self.assertEqual(
            merged.meta["layers"],
            [(0, 2, "main"), (2, 4, "commentary"), (4, 5, "main")],
        )
        # jdsw_self carried with the same per-part offset
        self.assertEqual(merged.meta["jdsw_self"], [(2, "音義"), (3, "曰")])

    def test_non_abutting_same_label_not_coalesced(self) -> None:
        a = KanripoDoc(
            id="KR0001_001",
            text="經注",
            meta={"layers": [(0, 1, "main"), (1, 2, "commentary")]},
        )
        b = KanripoDoc(
            id="KR0001_002",
            text="經",
            meta={"layers": [(0, 1, "main")]},
        )
        merged = merge_docs(a, b)
        # the two "main" spans are separated by a commentary span: keep distinct
        self.assertEqual(
            merged.meta["layers"],
            [(0, 1, "main"), (1, 2, "commentary"), (2, 3, "main")],
        )

    def test_spec_offsets_layers_and_jdsw_self_by_preceding_length(self) -> None:
        # text lengths 3 and 1; second part's spans shift by 3 (len of first)
        a = KanripoDoc(
            id="KR0001_001",
            text="天命之",  # len 3
            meta={
                "layers": [(0, 2, "main"), (2, 3, "commentary")],
                "jdsw_self": [(1, "音")],
            },
        )
        b = KanripoDoc(
            id="KR0001_002",
            text="性",  # len 1
            meta={"layers": [(0, 1, "main")], "jdsw_self": [(0, "義")]},
        )
        merged = merge_docs(a, b)
        self.assertEqual(
            merged.meta["layers"],
            [(0, 2, "main"), (2, 3, "commentary"), (3, 4, "main")],
        )
        self.assertEqual(merged.meta["jdsw_self"], [(1, "音"), (3, "義")])

    def test_no_source_layers_means_no_layers_key(self) -> None:
        a = KanripoDoc(id="KR0001_001", text="天", meta={"title": "t"})
        b = KanripoDoc(id="KR0001_002", text="命", meta={})
        merged = merge_docs(a, b)
        # no source carried layers/jdsw_self: don't fabricate empty ones,
        # but keep other caller meta (title) when passed explicitly
        self.assertNotIn("layers", merged.meta)
        self.assertNotIn("jdsw_self", merged.meta)
        self.assertEqual(merge_docs(a, b, meta={"title": "t"}).meta["title"], "t")

    def test_single_doc_merge_offsets_nothing(self) -> None:
        a = KanripoDoc(
            id="KR0001_001",
            text="經注",
            meta={"layers": [(0, 1, "main"), (1, 2, "commentary")], "jdsw_self": []},
        )
        merged = merge_docs(a)
        self.assertEqual(merged.meta["layers"], [(0, 1, "main"), (1, 2, "commentary")])
        self.assertEqual(merged.meta["jdsw_self"], [])
