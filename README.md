# Parsing phonology from the _Jingdian Shiwen_
This project is an attempt to convert the annotations compiled by the Tang dynasty scholar [Lu Deming (陸德明)](https://en.wikipedia.org/wiki/Lu_Deming) in the [_Jingdian Shiwen_ (经典释文)](https://en.wikipedia.org/wiki/Jingdian_Shiwen) into a structured form that matches individual characters to their Middle Chinese pronunciation.

Many of the annotations in the _Jingdian Shiwen_ specify how a particular character should be read, often using the [_fanqie_ (反切)](https://en.wikipedia.org/wiki/Fanqie) method. Some of these annotations follow a structure predictable enough to transform them into a reading, for which we use William Baxter's (1992) Middle Chinese transcription system<sup>1</sup>.

The source text used is from the Kanseki Repository, and is preprocessed to remove punctuation, whitespace, and any non-Chinese characters. The output format is a [CoNLL-like](https://universaldependencies.org/format.html) plaintext file that maps a single character to its annotation, one character per line, separated by a tab. The aim is to produce output that can be used for machine learning, natural language processing, and other computational applications.
## Usage
You can download a compressed archive of the entire project from the [releases page](https://github.com/direct-phonology/jdsw/releases). Alternatively, invididual chapters of the _Jingdian Shiwen_ are available as files in the [`out/`](out/) directory.
## Developing
To generate your own copy of the output, first pull down a copy of the source text:
```bash
git submodule update --init
```
Next, install python dependencies:
```bash
pip install -r requirements.txt
```
Then you can run the annotation process, which writes to `out/` by default:
```bash
bin/annotate.py
```
## Testing
You can run unit tests for the logic in the scripts with:
```bash
python -m unittest
```
## Updating
To get a fresh copy of the source text from upstream, you can run:
```sh
git submodule update --remote --merge
```
## License
Kanseki Repository text is licensed [CC-BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/legalcode). See [LICENSE](LICENSE).

---
<sup>1</sup> Baxter, William H. (1992), _A Handbook of Old Chinese Phonology_, Berlin: Mouton de Gruyter, ISBN 978-3-11-012324-1.
