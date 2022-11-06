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

st.title("NER pattern matching")

pattern_files = Path("assets").glob("*ner_patterns.jsonl")
pattern_file = st.selectbox("Select an NER pattern file", pattern_files)

if pattern_file:
    patterns = list(srsly.read_jsonl(pattern_file))
else:
    patterns = []

nlp = spacy.blank("och")
ruler = nlp.add_pipe("entity_ruler")
ruler.add_patterns(patterns)

dataset = load_data()
rows = []
for annotation in dataset["annotation"]:
    doc = nlp(annotation)
    for ent in doc.ents:
        rows.append({
            "text": ent.text,
            "label": ent.label_,
            "annotation": annotation,
            "title": dataset[dataset["annotation"] == annotation]["title"].values[0]
        })
hits = pd.DataFrame(rows, columns=["text", "label", "annotation", "title"])

st.write("## Found patterns")
total = len(pd.unique(hits["text"]))
st.write("### Total: {}".format(total))
top_n = st.slider("Show top: ", 1, total, 25)
top = pd.DataFrame(hits["text"].value_counts()[:top_n].rename_axis("pattern").reset_index(name="count"))
top["label"] = top["pattern"].apply(lambda x: hits[hits["text"] == x]["label"].values[0])
st.write(alt.Chart(top, width=700).mark_bar().encode(x=alt.X("pattern", sort=None), y="count", color="label"))

missing = set([pattern["pattern"] for pattern in patterns]) - set(hits["text"])
st.write("## Missing patterns")
st.write("### Total: {}".format(len(missing)))
st.write(", ".join(sorted(missing)))
