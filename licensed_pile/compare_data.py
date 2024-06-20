"""Compare pre and post processed dolma examples."""

import json
import textwrap

import smart_open
import streamlit as st

st.set_page_config(page_title="Compare", layout="wide")
st.title("Compare different versions of data.")


@st.cache_data
def load_data(old, new):
    with smart_open.open(old) as f:
        old = [json.loads(l) for l in f if l]
    with smart_open.open(new) as f:
        new = [json.loads(l) for l in f if l]
    return old, new


if "index" not in st.session_state:
    st.session_state.index = 0
# Don't set this here, as it will be set with the value of the number input.
# if "width" not in st.session_state:
#     st.session_state.width = 88

config = st.expander("config")

with config:
    old_path = st.text_input(label="Old Data")
    new_path = st.text_input(label="New Data")

    data_load_state = st.text(f"Loading data from:\n\t{old_path}\n\t{new_path}")

    old, new = load_data(old_path, new_path)

    data_load_state.text(f"Loaded {len(old)} examples")

    wrap_width = st.number_input("Wrap Width:", value=88, key="width")

    to_wrap = st.checkbox("Wrap?", value=True)


def update_index(i):
    st.session_state.index += i


def set_index(i):
    st.session_state.index = i


b1, b2 = st.columns(2)

with b1:
    p, n = st.columns(2)
    with p:
        st.button("prev", on_click=update_index, args=[-1])
    with n:
        st.button("next", on_click=update_index, args=[1])
with b2:
    index_input = st.number_input(
        "Index:", min_value=0, max_value=len(old), key="index"
    )

old_col, new_col = st.columns(2)


def wrap(text, width=88):
    lines = text.split("\n")
    new_lines = []
    for line in lines:
        if line:
            new_lines.extend(
                textwrap.wrap(
                    line, width=width, replace_whitespace=False, drop_whitespace=False
                )
            )
        else:
            new_lines.append("")
    return "\n".join(new_lines)


with old_col:
    st.subheader("Old Text")
    with st.container(height=500):
        if to_wrap:
            st.text(wrap(old[st.session_state.index]["text"], st.session_state.width))
        else:
            st.text(old[st.session_state.index]["text"])

with new_col:
    st.subheader("New Text")
    with st.container(height=500):
        if to_wrap:
            st.text(wrap(new[st.session_state.index]["text"], st.session_state.width))
        else:
            st.text(new[st.session_state.index]["text"])

st.header("Metadata")
st.json(old[st.session_state.index]["metadata"], expanded=False)
