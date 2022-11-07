"""Various streamlit-powered visualizations of the _Jingdian Shiwen_ data."""

import re
import streamlit as st
import pandas as pd
import spacy
from pathlib import Path
import srsly
import altair as alt
from spacy.matcher import Matcher

@st.cache
def load_data():
    """Load the data."""
    return pd.read_csv("assets/annotations.csv")

@st.cache
def get_hits(patterns):
    """Apply a list of patterns to the corpus. Returns hits and misses."""
    dataset = load_data()
    nlp = spacy.blank("och")
    ruler = nlp.add_pipe("entity_ruler")
    ruler.add_patterns(patterns)
    rows = []
    for annotation in dataset["annotation"]:
        doc = nlp(annotation)
        for ent in doc.ents:
            rows.append({
                "pattern": ent.text,
                "label": ent.label_,
                "annotation": annotation,
                "title": dataset[dataset["annotation"] == annotation]["title"].values[0]
            })
    hits = pd.DataFrame(rows, columns=["pattern", "label", "annotation", "title"])
    hit_patterns = hits["pattern"].unique()
    misses = pd.DataFrame([pattern for pattern in patterns if pattern not in hit_patterns], columns=["pattern", "label"])
    return hits, misses

def get_term_hits(term):
    """Search for a single term in the corpus. Returns hits only."""
    dataset = load_data()
    nlp = spacy.blank("och")
    # matcher = Matcher(nlp.vocab)
    # pattern = [{"TEXT": c} for c in term]
    # matcher.add(term, [pattern])
    try:
        pattern = re.compile(term)
    except re.error as e:
        st.error("Invalid regular expression")
        return pd.DataFrame([], columns=["match", "start", "end", "annotation", "title", "juan", "juan_title", "index", "headword"])
    rows = []
    for annotation in dataset["annotation"]:
        doc = nlp(annotation)
        for match in re.finditer(pattern, doc.text):
            rows.append({
                "match": match.group(0),
                "start": match.start(),
                "end": match.end(),
                "annotation": annotation,
                "headword": dataset[dataset["annotation"] == annotation]["headword"].values[0],
                "title": dataset[dataset["annotation"] == annotation]["title"].values[0],
                "juan": dataset[dataset["annotation"] == annotation]["juan"].values[0] or 1,
                "juan_title": dataset[dataset["annotation"] == annotation]["juan_title"].values[0],
                "index": dataset[dataset["annotation"] == annotation]["index"].values[0]
            })
    return pd.DataFrame(rows, columns=["match", "start", "end", "annotation", "title", "juan", "juan_title", "index", "headword"])

def files_tab():
    """NER pattern matching via a file of patterns."""
    # Load pattern from a file and calculate/cache hits and misses
    pattern_files = Path("assets").glob("*ner_patterns.jsonl")
    pattern_file = st.selectbox("Select an NER pattern file", pattern_files)
    if pattern_file:
        patterns = list(srsly.read_jsonl(pattern_file))
        hits, misses = get_hits(patterns)
    else:
        hits = pd.DataFrame(columns=["pattern", "label", "annotation", "title"])
        misses = pd.DataFrame(columns=["pattern", "label"])

    # Calculate total hits for each pattern
    total_hits = len(hits["pattern"].unique())
    total_misses = len(misses["pattern"].unique())
    hit_counts = pd.DataFrame(hits["pattern"].value_counts().rename_axis("pattern").reset_index(name="count"))
    hit_counts["label"] = hit_counts["pattern"].apply(lambda x: hits[hits["pattern"] == x]["label"].values[0])
    top_n = st.slider("Show top: ", 1, total_hits, 10)

    # Show chart and table of top n hit patterns, broken out by label
    st.write("## Found patterns")
    st.write("### Total: {}".format(total_hits))
    st.write(alt.Chart(hit_counts[:top_n], width=700).mark_bar().encode(x=alt.X("pattern", sort=None), y="count", color="label"))
    st.table(hit_counts.loc[:,["count", "pattern", "label"]][:top_n])

    # Show table of missing patterns, limit to n
    st.write("## Missing patterns")
    st.write("### Total: {}".format(total_misses))
    st.table(misses[:top_n])

def interactive_tab():
    """NER pattern matching via interactive input."""
    term = st.text_input("Enter a search term")
    if term:
        hits = get_term_hits(term)
        hit_annotations = hits["annotation"].unique()
        st.write("_{} hits in {} annotations_".format(len(hits), len(hit_annotations)))

        # Show chart of results by match text
        if hits["match"].unique().size > 1:
            st.write("### Match types")
            hit_counts = pd.DataFrame(hits["match"].value_counts().rename_axis("match").reset_index(name="count"))
            st.write(alt.Chart(hit_counts[:10], width=700).mark_bar().encode(x=alt.X("match", sort=None), y="count"))

        # Show list of search results
        for title, title_group in hits.groupby("title"):
            st.write("### {}".format(title))
            for juan_no, juan_group in title_group.groupby("juan"):
                st.write("#### {}《{}》".format(int(juan_no), juan_group["juan_title"].values[0]))
                for annotation, annotation_group in juan_group.groupby("annotation"):
                    starts = annotation_group["start"].values
                    ends = annotation_group["end"].apply(lambda x: x - 1).values
                    headword = annotation_group["headword"].values[0]
                    highlighted_annotation = ""
                    for i, char in enumerate(annotation):
                        if i in starts:
                            highlighted_annotation += "<mark>"
                        highlighted_annotation += char
                        if i in ends:
                            highlighted_annotation += "</mark>"
                    st.write("<li class='annotation'>{} ({})</li>".format(headword, highlighted_annotation), unsafe_allow_html=True)

def main():
    # Prevent displaying row indices
    # https://docs.streamlit.io/knowledge-base/using-streamlit/hide-row-indices-displaying-dataframe
    hide_table_row_index = """
    <style>
    thead tr th:first-child { display: none; }
    tbody th { display: none; }
    </style>
    """
    st.markdown(hide_table_row_index, unsafe_allow_html=True)

    # Styles for annotation highlighting
    highlight_match = """
    <style>
    .annotation { font-family: serif; }
    mark { background-color: #ffd700; color: #000; }
    </style>
    """
    st.markdown(highlight_match, unsafe_allow_html=True)

    # Render the main title and tabs
    st.title("NER pattern matching")
    tab1, tab2 = st.tabs(["Pattern file search", "Interactive search"])
    with tab1:
        files_tab()
    with tab2:
        interactive_tab()

if __name__ == "__main__":
    main()
