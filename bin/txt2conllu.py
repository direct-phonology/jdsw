#!/usr/bin/env python3

import sys

import typer

from lib.util import (
    convert_krp_entities,
    clean_org_text,
    get_org_metadata,
    strip_punctuation,
    split_sentences,
)
from lib.patterns import PARAGRAPH_NUMBER, CHAPTER_HEADER


def main() -> None:
    """Convert a Kanseki Repository text into CoNLL-U format."""

    # read everything from stdin
    text = sys.stdin.read()

    # get text metadata
    metadata = get_org_metadata(text)

    # convert entities to unicode & clean org-mode artifacts
    text = convert_krp_entities(text)
    text = clean_org_text(text)

    # remove pilcrows
    text = text.replace("¶", "")

    # generate doc and doc identifier
    doc = []
    doc_id = metadata["id"]

    # extract chapters (split on CHAPTER_NUMBER)
    for i, chapter in zip(
        CHAPTER_HEADER.split(text)[1::3], CHAPTER_HEADER.split(text)[::3][1:]
    ):
        chapter_id = f"{doc_id}.{i}"

        # extract paragraphs (split on PARAGARAPH_NUMBER)
        for j, paragraph in enumerate(PARAGRAPH_NUMBER.split(chapter)[::2][1:]):

            # generate paragraph and its id
            paragraph_id = f"{chapter_id}.{j+1}"
            sentences = []

            # extract sentences from each paragraph
            for k, sentence in enumerate(split_sentences(paragraph)):

                # remove line breaks and whitespace
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
