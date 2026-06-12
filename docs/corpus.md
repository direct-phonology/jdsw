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

The SBCK 莊子 embeds Lu Deming's own 音義 inline (「音義曰…」 inside the
commentary). This is a contamination risk for alignment — the JDSW's own text
must not be matched as if it were Guo Xiang's — and at the same time a second
witness of the JDSW itself. The 注疏 editions KR1e0006 (公羊注疏) and
KR1e0010 (穀梁注疏) likewise credit 陸德明 and embed the 音義 inline.

## Edition mismatches per work

### 老子 — swapped

The SBCK witness (KR5c0065) is the 河上公章句, but Lu Deming's 老子音義 keys
to the 王弼本: misses like 聖人之治 and 夫執一家之量 are phrases from Wang
Bi's commentary that simply don't exist in Heshanggong. `docs.csv` now points
to **KR5c0073 道德真經註(二), 王弼, ZTDZ (正統道藏) branch** — there is no
SBCK witness of the Wang Bi Laozi. Tested: 64.9% → 92.2% matched, residual
misses are ordinary variant graphs.

Caveats: the Daozang transcription writes the commentary full-size with no
parenthesis markup, so main-vs-commentary layer detection needs a positional
heuristic for this witness (commentary follows each 經 segment) rather than
the paren-stripping used for SBCK texts. KR5c0046 (道德經古本篇, 傅奕本) is
worth pulling as a comparandum, since Lu repeatedly cites 古本 readings.
`annotations.jsonl` still records `zhengwen_id: KR5c0057` until the corpus is
re-exported against the new witness.

### 孝經 — no clean swap exists

Lu's 孝經音義 keys to the 鄭氏注, which is lost; the Qing reconstructions of
it were built partly from the JDSW itself. KR1f0002 is the Tang imperial
commentary (御注); KR1f0003 (古文孝經孔氏傳, WYG branch) and KR1f0004
(孝經注疏) don't contain Zheng's commentary either. Policy: **align only
經-layer lemmata** and treat the 注-layer lemmata as the project's output
rather than its input — a structured JDSW is itself a witness for
reconstructing the lost 鄭注. Lemmata where Lu notes 「本今無此字」 should
additionally be checked against KR1f0003's 古文 recension.

### 儀禮 and 公羊傳 — dropping the CHANT dependency

The Kanripo catalog lists 正文 editions (KR1d0025, KR1e0005, keyed to the
1816 南昌府學 阮元 reprints) but both are catalog stubs with no repository.
Instead, derive the 正文 from the commentary editions already in `docs.csv`
(KR1d0026 儀禮鄭注, KR1e0007 公羊解詁) by stripping the parenthesized
commentary — the pipeline already produces this as a byproduct, it guarantees
offset compatibility with the alignment, and it aligns at 96.9%/97.2%.

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
