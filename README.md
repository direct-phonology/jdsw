<!-- SPACY PROJECT: AUTO-GENERATED DOCS START (do not remove) -->

# 🪐 spaCy Project: Parsing the _Jingdian Shiwen_

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://direct-phonology-jdsw-scriptsvisualize-0px83h.streamlit.app/)

This project is an attempt to convert the annotations compiled by the Tang dynasty scholar [Lu Deming (陸德明)](https://en.wikipedia.org/wiki/Lu_Deming) in the [_Jingdian Shiwen_ (经典释文)](https://en.wikipedia.org/wiki/Jingdian_Shiwen) into a structured form that separates phonology, glosses, and references to secondary sources. A [spaCy](https://spacy.io/) pipeline is configured to parse and tag the annotations, and [prodigy](https://prodi.gy/) is used for guided annotation of the training data.

The source text used is from the [Kanseki Repository](https://www.kanripo.org/), and has been preprocessed to remove punctuation, whitespace, and any non-Chinese characters. The results are saved in JSON-lines (`.jsonl`) format, with the aim being output that can be used for machine learning, natural language processing, and other computational applications.

## Annotating data
To annotate training data, you need to have spacy installed in your python environment:
```sh
pip install spacy
```
You also need a copy of [prodigy](https://prodi.gy/). Once you have the appropriate wheel, install it with:
```sh
# example: prodigy version 1.11.8 for python 3.10 on windows
pip install prodigy-1.11.8-cp310-cp310-win_amd64.whl
```
Then, verify the project assets are downloaded:
```sh
spacy project assets
```
Install python dependencies needed for annotation:
```sh
spacy project run install
```
Then, choose an annotation task (see "commands" below). Invoke it with:
```sh
# example: annotate parts-of-speech
spacy project run pos
```


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
| `pos` | Annotate parts of speech by correcting an existing model |

### 🗂 Assets

The following assets are defined by the project. They can
be fetched by running [`spacy project assets`](https://spacy.io/api/cli#project-assets)
in the project directory.

| File | Source | Description |
| --- | --- | --- |
| [`assets/annotations.jsonl`](assets/annotations.jsonl) | Local | Corpus of annotations from the _Jingdian Shiwen_, including their headwords. |
| [`assets/ner_patterns.jsonl`](assets/ner_patterns.jsonl) | Local | Patterns for pre-selecting regions in annotation text. |

<!-- SPACY PROJECT: AUTO-GENERATED DOCS END (do not remove) -->
