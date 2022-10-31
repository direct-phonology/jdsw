<!-- SPACY PROJECT: AUTO-GENERATED DOCS START (do not remove) -->

# 🪐 spaCy Project: Parsing the _Jingdian Shiwen_

This project is an attempt to convert the annotations compiled by the Tang dynasty scholar [Lu Deming (陸德明)](https://en.wikipedia.org/wiki/Lu_Deming) in the [_Jingdian Shiwen_ (经典释文)](https://en.wikipedia.org/wiki/Jingdian_Shiwen) into a structured form that separates phonology, glosses, and references to secondary sources. A [spaCy](https://spacy.io/) pipeline is configured to parse and tag the annotations, and [prodigy](https://prodi.gy/) is used for guided annotation of the training data.

The source text used is from the [Kanseki Repository](https://www.kanripo.org/), and has been preprocessed to remove punctuation, whitespace, and any non-Chinese characters. The results are saved in JSON-lines (`.jsonl`) format, with the aim being output that can be used for machine learning, natural language processing, and other computational applications.


## 📋 project.yml

The [`project.yml`](project.yml) defines the data assets required by the
project, as well as the available commands and workflows. For details, see the
[spaCy projects documentation](https://spacy.io/usage/projects).

### ⏯ Commands

The following commands are defined by the project. They
can be executed using [`spacy project run [name]`](https://spacy.io/api/cli#project-run).
Commands are only re-run if their inputs have changed.

| Command | Description |
| --- | --- |
| `install` | Install dependencies |
| `ner_manual` | Mark people and works referenced in annotations |

### 🗂 Assets

The following assets are defined by the project. They can
be fetched by running [`spacy project assets`](https://spacy.io/api/cli#project-assets)
in the project directory.

| File | Source | Description |
| --- | --- | --- |
| [`instructions.html`](instructions.html) | Local | HTML file with annotation instructions. |
| [`prodigy.json`](prodigy.json) | Local | Prodigy configuration file. |
| [`assets/annotations.jsonl`](assets/annotations.jsonl) | Local | Corpus of annotations from the _Jingdian Shiwen_, including their headwords. |
| [`assets/ner-patterns.jsonl`](assets/ner-patterns.jsonl) | Local | Patterns for pre-selecting regions in annotation text. |

<!-- SPACY PROJECT: AUTO-GENERATED DOCS END (do not remove) -->
