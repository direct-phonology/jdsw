"""Various streamlit-powered visualizations of the _Jingdian Shiwen_ data."""

import streamlit as st
import pandas as pd
import spacy
from pathlib import Path
import srsly
import altair as alt

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

def main():
    # Prevent displaying row indices
    # https://docs.streamlit.io/knowledge-base/using-streamlit/hide-row-indices-displaying-dataframe
    hide_table_row_index = """
    <style>
    thead tr th:first-child {display:none}
    tbody th {display:none}
    </style>
    """
    st.markdown(hide_table_row_index, unsafe_allow_html=True)
    st.title("NER pattern matching")

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

if __name__ == "__main__":
    main()
