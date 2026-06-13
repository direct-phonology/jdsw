# Corpus alignment notes

Findings from running the anchor/LIS aligner against the full corpus
(June 2026). These constraints are easy to violate silently; read this before
re-running alignment or swapping editions.

## Annotation ordering

`index` in `annotations.jsonl` restarts per JDSW physical sub-juan, while
`juan_id` tracks the commented work's chapters. Whenever a chapter spans a
JDSW 卷 boundary, sorting by `(juan_id, index)` interleaves multiple lemma
sequences — 昭公 (KR1e0001_010) blends seven sub-files with thousands of
colliding index values. Since every alignment strategy depends on the
monotonic order of lemmata, this poisons results downstream (左傳 collapsed
to 47% under the wrong sort; 97% under the right one).

**The correct global order is `(jdsw_id, index)`.** Every entry now also
carries an explicit `meta.sequence` (written by
`scripts/bin/resequence_annotations.py`); prefer sorting by it.

## Kanripo branches

`git clone` of a Kanripo repository gives you the default branch, which is
the HFL witness — for 莊子 (KR5c0051) that is bare text with no 郭象注 at
all, so every commentary lemma misses. Any tooling that fetches sources must
pin the branch explicitly; `assets/docs.csv` now records the required branch
per work (`sbck_branch`).

The SBCK 莊子 embeds Lu Deming's own 音義 inline, inside Guo Xiang's
parenthesized commentary. This is a contamination risk for alignment — the
JDSW's own text must not be matched as if it were Guo Xiang's — and at the
same time a second witness of the JDSW itself. `ExtractLayers`
(`scripts/lib/transforms.py`) pulls these segments into `doc.meta["jdsw_self"]`
so they are excluded from candidate enumeration: the 篇-initial 音義 block is
opened by the phrase 音義曰, and each later block by a circle (〇/○), so both
are registered as embedded-音義 markers. With this in place 莊子 卷 26 aligns
at ~0.98 (逍遙遊 n=251). The 注疏 editions KR1e0006 (公羊注疏) and KR1e0010
(穀梁注疏) likewise credit 陸德明 and embed the 音義 inline, and so does the
SBCK 公羊解詁 (KR1e0007) now used as the 公羊 witness — see the 儀禮/公羊
section below for the 〇-span exclusion this requires.

## Edition mismatches per work

### 老子 — swapped

The SBCK witness (KR5c0065) is the 河上公章句, but Lu Deming's 老子音義 keys
to the 王弼本: misses like 聖人之治 and 夫執一家之量 are phrases from Wang
Bi's commentary that simply don't exist in Heshanggong. `docs.csv` now points
to **KR5c0073 道德真經註(二), 王弼, ZTDZ (正統道藏) branch** — there is no
SBCK witness of the Wang Bi Laozi. Tested: 64.9% → 92.2% matched, residual
misses are ordinary variant graphs.

Caveats: the Daozang transcription writes the commentary full-size with no
parenthesis markup, so the paren-based `ExtractLayers` finds no commentary
and (correctly) refuses to guess — it labels the whole witness `unknown`
rather than a falsely-confident `main`, and `layer_at` likewise falls back to
`unknown` for any uncovered position. Trustworthy 經/注 labels for this
witness still need a positional heuristic (commentary follows each 經
segment), most cleanly by aligning a bare 經 witness against the combined
text and labeling the gaps 注; that is unwritten, so 老子 layer labels read
`unknown` until then. KR5c0046 (道德經古本篇, 傅奕本) is worth pulling as a
comparandum, since Lu repeatedly cites 古本 readings. `annotations.jsonl`
still records `zhengwen_id: KR5c0057` until the corpus is re-exported against
the new witness.

### 孝經 — no clean swap exists

Lu's 孝經音義 keys to the 鄭氏注, which is lost; the Qing reconstructions of
it were built partly from the JDSW itself. KR1f0002 is the Tang imperial
commentary (御注); KR1f0003 (古文孝經孔氏傳, WYG branch) and KR1f0004
(孝經注疏) don't contain Zheng's commentary either. Policy: **align only
經-layer lemmata** and treat the 注-layer lemmata as the project's output
rather than its input — a structured JDSW is itself a witness for
reconstructing the lost 鄭注. Lemmata where Lu notes 「本今無此字」 should
additionally be checked against KR1f0003's 古文 recension.

### 儀禮 and 公羊傳 — swapped (CHANT dependency dropped)

The Kanripo catalog lists 正文 editions (KR1d0025, KR1e0005, keyed to the
1816 南昌府學 阮元 reprints) but both are catalog stubs with no repository.
Instead, the 正文 is derived from the commentary editions in `docs.csv`
(KR1d0026 儀禮鄭注, KR1e0007 公羊解詁) by keeping only the main-layer
characters — the layer extractor produces this as a byproduct, and it
guarantees offset compatibility with the full-edition alignment, which a
separately-sourced text never could. Accordingly the `zhengwen_id` column is
empty for these two works in `docs.csv` and `juan.csv`; with the CHANT texts
gone, the whole corpus comes from a single source (Kanripo, CC-BY) with one
acquisition path (`git clone -b $sbck_branch`).

Confirmed against fresh clones (June 2026), JDSW 卷 10 and 21 with layer
tracking: 儀禮 97.7% matched (n=3,227), 公羊 97.2% (n=2,674), reproducing the
figures originally recorded here (96.9%/97.2%). ~58% of matched lemmata in
both works sit in the commentary layer — Lu glosses 鄭注 and 何休's 解詁 as
heavily as the classics — so the bare-正文 CHANT texts could never have
captured the majority of these chapters; the swap roughly doubles the
recoverable data. Residual misses are ordinary variant-graph residue
(袗𤣥, 紒, 齊衰), i.e. the usual `variants.json` harvesting queue.

**Trap: KR1e0007 embeds the JDSW itself.** The SBCK 公羊解詁 carries Lu
Deming's 音義 inline as 〇-prefixed paren spans — (〇陸曰解詁佳買反…),
(〇正月音征又音政後放此) — over 400 in the first three juan alone. The
97.2% figure was computed with those spans dropped during cleaning; without
that exclusion the JDSW matches its own embedded text and the numbers are
inflated and wrong. The layer extractor therefore needs a third label
(`jdsw_self`) for this witness, exactly as planned for the 莊子 音義曰 spans
(see "Kanripo branches" above) — the 〇 marker makes it mechanically trivial
here. KR1d0026 is clean (zero 〇 spans). Silver lining: the embedded spans
are a second in-situ witness of the 公羊音義 — useful for collation against
the SBCK JDSW transcription and as another free gold-standard set for
evaluating the aligner, same as the Wikisource 孝經鄭注.

`annotations.jsonl` still records `zhengwen_id: CH1e0873_*` / `CH1e0877_*`
until the corpus is re-exported against the new witnesses (same situation as
the 老子 KR5c0057 residue above).

### 尚書 — permanent residue

The ~10% misses are not edition-swappable: Lu's lemmata preserve pre-衛包
(隸古定) graphs and no pre-reform received text exists. Treat as recension
residue, not alignment error.

## Character-level gaps

- Variant pairs surfaced by fuzzy matches are added to `assets/variants.json`
  as found (e.g. 䘮/喪, 弑/殺, 恱/說/説/悦). Partial matches in the alignment
  report are the queue for finding more.
- Lemmata whose gloss cites their own alternative graph (本又作X / 本亦作X,
  including chains 本又作X又作Y) are retried with the cited graph substituted
  — see `alternate_graphs` in `scripts/lib/alignment.py` (confidence
  `alternate`).
- The damaged-character placeholder ⬤ in SBCK transcriptions is treated as a
  wildcard during gap-filling rather than being absorbed by lossy prefix
  matches.
- ~47 headwords contain Kanripo private-use entities missing from
  `kr-unicode.csv`; these need mapping additions before they can align.

## Reading extraction beyond fanqie

`scripts/lib/polyphone.py` derives a reading per character occurrence from
four sources, tagged in each record's `kind`:

- **fanqie** (X Y 反) and **duruo** (音 X) — the explicit readings, composed
  or looked up against the Guangyun.
- **ruzi** — 如字 ("read as usual", ~5% of annotations) declines a special
  reading, so the character keeps its *default*. The default is not derivable
  from the gloss; it comes from `assets/default_reading_profiles.csv` (column
  `ruzi_default`, with `ruzi_confidence`/`signals_agree`), an elimination
  analysis carried in as an asset and read by `scripts/lib/ruzi.py`. Only the
  ~60 characters the analysis could resolve confidently carry a default; the
  rest stay unresolved (the table is deliberately conservative). Confidence
  and agreement ride along on each `ruzi` record so consumers can filter.
- **scope** — 下同 ("same below") and 注同 ("same in the 注") propagate an
  explicit reading to later occurrences of the same character, up to the next
  gloss of it (capped at `MAX_SCOPE`). 注同 is layer-aware: it propagates only
  to commentary-layer positions, so it depends on the layer extraction above
  and yields nothing on a witness whose layers are `unknown`.

Each of these multiplies usable labels beyond the bare fanqie count; 如字 and
the scope markers are each ~5% of annotations.
