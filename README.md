<!-- SPACY PROJECT: AUTO-GENERATED DOCS START (do not remove) -->

# 🪐 spaCy Project: Parsing the _Jingdian Shiwen_

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://direct-phonology-jdsw-scriptsvisualize-0px83h.streamlit.app/)

This project is an attempt to convert the annotations compiled by the Tang dynasty scholar [Lu Deming (陸德明)](https://en.wikipedia.org/wiki/Lu_Deming) in the [_Jingdian Shiwen_ (经典释文)](https://en.wikipedia.org/wiki/Jingdian_Shiwen) into a structured form that separates phonology, glosses, and references to secondary sources. A [spaCy](https://spacy.io/) pipeline is configured to parse and tag the annotations, and [prodigy](https://prodi.gy/) is used for guided annotation of the training data. The project is part of a broader effort to build a linguistic model of [Old Chinese (上古漢語)](https://en.wikipedia.org/wiki/Old_Chinese) that incoporates phonology.

## Data
The _Jingdian Shiwen_ comprises Lu's annotations on most of the ["Thirteen Classics" (十三經)](https://en.wikipedia.org/wiki/Thirteen_Classics) of the Confucian tradition, as well as some Daoist texts. We use the edition of the _Jingdian Shiwen_ found in the [_Collectanea of the Four Categories_ (四部叢刊)](http://www.chinaknowledge.de/Literature/Poetry/sibucongkan.html), which includes high-quality lithographic reproductions of many ancient texts. The annotations given in the _Jingdian Shiwen_ are paired with the source texts to which they apply; for this we predominantly use the definitive (正文) editions published by the [Kanseki Repository](https://www.kanripo.org/).

|work|title|source|_Jingdian Shiwen_ chapters (卷)|
|-|-|-|-|
|周易|[_Book of Changes_](https://en.wikipedia.org/wiki/I_Ching)|[KR1a0001](https://github.com/kanripo/KR1a0001)|2
|尚書|[_Book of Documents_](https://en.wikipedia.org/wiki/Book_of_Documents)|[KR1b0001](https://github.com/kanripo/KR1b0001)|3-4|
|毛詩|[_Mao Commentary_](https://en.wikipedia.org/wiki/Mao_Commentary) on the [_Book of Odes_](https://en.wikipedia.org/wiki/Classic_of_Poetry)|[KR1c0001](https://github.com/kanripo/KR1c0001)|5-7|
|周禮|[_Rites of Zhou_](https://en.wikipedia.org/wiki/Rites_of_Zhou)|[KR1d0001](https://github.com/kanripo/KR1d0001)|8-9|
|儀禮|[_Etiquette and Ceremonial_](https://en.wikipedia.org/wiki/Etiquette_and_Ceremonial)|CH1e0873*|10|
|禮記|[_Book of Rites_](https://en.wikipedia.org/wiki/Book_of_Rites)|[KR1d0052](https://github.com/kanripo/KR1d0052)|11-14|
|春秋左傳|[_Commentary of Zuo_](https://en.wikipedia.org/wiki/Zuo_Zhuan) on the [_Spring and Autumn Annals_](https://en.wikipedia.org/wiki/Spring_and_Autumn_Annals)|[KR1e0001](https://github.com/kanripo/KR1e0001)|15-20|
|春秋公羊傳|[_Commentary of Gongyang_](https://en.wikipedia.org/wiki/Gongyang_Zhuan) on the [_Spring and Autumn Annals_](https://en.wikipedia.org/wiki/Spring_and_Autumn_Annals)|CH1e0877*|21|
|春秋穀梁傳|[_Commentary of Guliang_](https://en.wikipedia.org/wiki/Guliang_Zhuan) on the [_Spring and Autumn Annals_](https://en.wikipedia.org/wiki/Spring_and_Autumn_Annals)|[KR1e0008](https://github.com/kanripo/KR1e0008)|22|
|孝經|[_Classic of Filial Piety_](https://en.wikipedia.org/wiki/Classic_of_Filial_Piety)|[KR1f0001](https://github.com/kanripo/KR1f0001)|23|
|論語|[_Analects of Confucius_](https://en.wikipedia.org/wiki/Analects)|[KR1h0004](https://github.com/kanripo/KR1h0004)|24|
|老子|[_Laozi_](https://en.wikipedia.org/wiki/Tao_Te_Ching)|[KR5c0057](https://github.com/kanripo/KR5c0057)|25|
|莊子|[_Zhuangzi_](https://en.wikipedia.org/wiki/Zhuangzi_(book))|[KR5c0126](https://github.com/kanripo/KR5c0126)|26-28|

*This data is sourced with permission from the [China Ancient Texts (CHANT) database](https://www.cuhk.edu.hk/ics/rccat/en/database.html).

We omit chapter 1 of the _Jingdian Shiwen_, corresponding to the [_Erya_ (爾雅)](https://en.wikipedia.org/wiki/Erya). All digital sources have been preprocessed to remove punctuation, whitespace, and non-Chinese characters. Kanseki Repository data is generously licensed CC-BY.

After processing, the labeled output data is saved in JSON-lines (`.jsonl`) format, to be used for machine learning, natural language processing, and other computational applications.

## Annotating
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
| [`assets/annotations.jsonl`](assets/annotations.jsonl) | Local | Corpus of annotations from the _Jingdian Shiwen_, including their headwords |
| [`assets/corpus.jsonl`](assets/corpus.jsonl) | Local | Corpus of source texts annotated in the _Jingdian Shiwen_, divided into documents |
| [`assets/docs.csv`](assets/docs.csv) | Local | Table mapping each chapter in a source text to its location in the _Jingdian Shiwen_ |
| [`assets/variants.json`](assets/variants.json) | Local | Equivalency table for graphic variants of characters |

<!-- SPACY PROJECT: AUTO-GENERATED DOCS END (do not remove) -->
