#!/usr/bin/env python3

import pathlib
from xml.etree import ElementTree as ET

import typer

from lib.patterns import PARAGRAPH_NUMBER
from lib.util import split_sentences, strip_punctuation

# namespace helper
NS = {
    "tei": "http://www.tei-c.org/ns/1.0",
    "xml": "http://www.w3.org/XML/1998/namespace",
}


def main(file: pathlib.Path) -> None:
    """Convert a Kanseki Repository XML text into CoNLL-U format."""

    # read file and parse TEI XML
    tree = ET.parse(str(file))
    tei = tree.getroot()

    # generate doc and doc identifier
    doc = []
    try:
        doc_id = tei.attrib["{http://www.w3.org/XML/1998/namespace}id"]
    except KeyError:
        typer.echo(f"No doc id found in {file}, using filename", err=True)
        doc_id = file.stem

    # extract chapters
    chapters = tree.findall("./tei:text/tei:body/tei:div", NS)
    for i, chapter in enumerate(chapters):
        chapter_id = f"{doc_id}-{i+1}"

        # extract paragraphs
        paragraphs = chapter.findall("tei:p", NS)
        for j, paragraph in enumerate(paragraphs):

            paragraph_id = f"{chapter_id}.{j+1}"
            sentences = []

            # extract sentences from each paragraph
            paragraph_text = "".join(
                [seg.text or "" for seg in paragraph.findall("tei:seg", NS)]
            ).strip()
            *_, ptext = PARAGRAPH_NUMBER.split(paragraph_text)
            for k, sentence in enumerate(split_sentences(ptext)):

                # remove line breaks
                sentence_text = "".join(sentence.split()).strip()

                # remove punctuation
                sentence_text = strip_punctuation(sentence_text)
                if not sentence_text:
                    continue

                # set the sentence id for each sentence
                sentence_id = f"{paragraph_id}.{k+1}"

                # tokenize by character with indices in CoNLL-U format
                sentence_tokens = "\n".join(
                    [
                        f"{l+1}\t{token}\t_\t_\t_\t_\t_\t_\t_\tSpaceAfter=No"
                        for l, token in enumerate(sentence_text)
                    ]
                )

                # generate the CoNLL-U sentence
                sentences.append(
                    f"# sent_id = {sentence_id}\n"
                    f"# text = {sentence_text}\n"
                    f"{sentence_tokens}"
                )

            if sentences:
                # add paragraph id to each first sentence of the paragraph
                sentences[0] = f"# newpar id = {paragraph_id}\n{sentences[0]}"

                # append all sentences to the doc
                doc += sentences

    # set the doc id for the first sentence in the doc
    doc[0] = f"# newdoc id = {doc_id}\n{doc[0]}"

    # serialize the CoNLL-U output
    output = "\n\n".join(doc)

    # write to stdout
    typer.echo(output.strip())


if __name__ == "__main__":
    typer.run(main)

__doc__ = main.__doc__  # type: ignore
