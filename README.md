# Parsing phonology from the _Jingdian Shiwen_
_**Note:** This repository is under active development and isn't yet ready for use!_

This project is an attempt to convert the annotations compiled by the Tang dynasty scholar [Lu Deming (陸德明)](https://en.wikipedia.org/wiki/Lu_Deming) in the [_Jingdian Shiwen_ (经典释文)](https://en.wikipedia.org/wiki/Jingdian_Shiwen) into a structured form that matches individual characters to their Middle Chinese pronunciation.

Many of the annotations in the _Jingdian Shiwen_ specify how a particular character should be read, often using the [_fanqie_ (反切)](https://en.wikipedia.org/wiki/Fanqie) method. Some of these annotations follow a structure predictable enough to transform them into a reading, for which we use [William Baxter's (1992) transcription for Middle Chinese](https://en.wikipedia.org/wiki/Baxter%27s_transcription_for_Middle_Chinese)<sup>1</sup>.

The source text used is from the Kanseki Repository, and is preprocessed to remove punctuation, whitespace, and any non-Chinese characters. The output format is a [CoNLL-U](https://universaldependencies.org/format.html) file that stores phonological information in the `MISC` field. The aim is to produce output that can be used for machine learning, natural language processing, and other computational applications.
## Usage
You can download a compressed archive of the entire project from the [releases page](https://github.com/direct-phonology/jdsw/releases). Alternatively, individual works annotated in the _Jingdian Shiwen_ are available as CoNLL-U files in the [`out/`](out/) directory.
## Developing
To generate your own copy of the output, first pull down a copy of the repository:
```bash
git clone https://github.com/direct-phonology/jdsw.git
```
Next, install python dependencies:
```bash
pip install -r requirements.txt
```
Then you can run the scripts in `bin/`:
```bash
python bin/test_pipe.py
```
## Testing
You can run unit tests for the logic in the scripts with:
```bash
python -m unittest
```
## License
Code in this repository is licensed under the [MIT License](./LICENSE). Kanseki Repository text is licensed [CC-BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/legalcode).

---
<sup>1</sup> Baxter, William H. (1992), _A Handbook of Old Chinese Phonology_, Berlin: Mouton de Gruyter, ISBN 978-3-11-012324-1.
