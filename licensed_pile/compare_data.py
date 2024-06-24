"""Compare pre and post processed dolma examples."""

import collections
import json
import textwrap

import smart_open
import streamlit as st

st.set_page_config(page_title="Compare", layout="wide")
st.title("Compare different versions of data.")

Index = collections.namedtuple("Index", ["old", "new"])


@st.cache_data
def load_data(old, new):
    with smart_open.open(old) as f:
        old = [json.loads(l) for l in f if l]
    with smart_open.open(new) as f:
        new = [json.loads(l) for l in f if l]
    old_idx = {o["id"]: i for i, o in enumerate(old)}
    new_idx = {n["id"]: i for i, n in enumerate(new)}
    # The ids aren't ordered so we can't to a posting merge like an inverted index
    new_k = set(new_idx.keys())
    # Instead iterate though old idx and check if they live in the new, this
    # will maintain the order as if we are looking line-by-line in the file while
    # making sure that the two documents are aligned in the case of a record being
    # deleted via preprocessing (we shouldn't see new ones get made).
    both = [k for k in old_idx if k in new_k]
    index = {k: Index(old_idx[k], new_idx[k]) for k in both}
    # old: A list of examples
    # new: A list of examples
    # index: A Dict mapping id: str -> (position in old, position in new)
    return old, new, index


config = st.expander("config")

with config:
    old_path = st.text_input(label="Old Data")
    new_path = st.text_input(label="New Data")

    data_load_state = st.text(f"Loading data from:\n\t{old_path}\n\t{new_path}")

    old, new, index = load_data(old_path, new_path)
    # When paging though examples by position (next/prev) this maps the position
    # to the id of an example
    by_position = list(index.keys())
    # When you jump to a given id, this can be used to find the logical position
    # of that example as if you hit next/back a bunch. Note: This position is
    # not related to the position in the old/new example list.
    by_id = {k: i for i, k in enumerate(by_position)}
    # Create a mapping from ids to title for easier exploration.
    id_to_title = {
        id: title
        for id, idx in index.items()
        if (title := new[idx.new].get("metadata", {}).get("title"))
    }
    title_to_id = {t: i for i, t in id_to_title.items()}

    data_load_state.text(f"Loaded {len(old)} examples")

    # Display Configuration
    wrap_width = st.number_input("Wrap Width:", value=88, key="width")
    to_wrap = st.checkbox("Wrap?", value=True)
    container_height = st.number_input("Text Hight:", value=500, key="height")

if "index" not in st.session_state:
    st.session_state.index = 0
if "id" not in st.session_state:
    st.session_state.id = by_position[st.session_state.index]
# Don't set this here, as it will be set with the value of the number input.
# if "width" not in st.session_state:
#     st.session_state.width = 88
# if "height" not in st.session_state:
#     st.session_state.width = 500


def update_index(i):
    # Don't go outside the bounds.
    if st.session_state.index == 0 and i < 0:
        return
    if st.session_state.index == len(by_position) - 1 and i > 0:
        return
    # We hit next/prev, so update the position.
    st.session_state.index += i
    # Now convert that position into an id
    st.session_state.id = by_position[st.session_state.index]
    if id_to_title:
        st.session_state.title = id_to_title[st.session_state.id]


def fix_by_id():
    # When the id is updated by a widget, make sure the index is updated to the
    # correct position.
    st.session_state.index = by_id[st.session_state.id]
    if id_to_title:
        st.session_state.title = id_to_title[st.session_state.id]


def fix_by_index():
    # When the position is updated by a widget, make sure the id is updated too.
    st.session_state.id = by_position[st.session_state.index]
    if id_to_title:
        st.session_state.title = id_to_title[st.session_state.id]


def fix_by_title():
    if id_to_title:
        id = title_to_id[st.session_state.title]
        st.session_state.id = id
        st.session_state.index = by_id[st.session_state.id]


# Display the controls
b1, b2 = st.columns(2)
# Previous and Next Buttons
with b1:
    st.button("prev", on_click=update_index, args=[-1])
    st.button("next", on_click=update_index, args=[1])
# Jump around widgets
with b2:
    index_input = st.number_input(
        "Index:",
        min_value=0,
        max_value=len(by_position) - 1,
        on_change=fix_by_index,
        key="index",
    )
    id_input = st.selectbox("Id:", options=by_position, on_change=fix_by_id, key="id")
    if id_to_title:
        title_input = st.selectbox(
            "Title:", options=title_to_id.keys(), on_change=fix_by_title, key="title"
        )


def wrap(text, width=88):
    r"""Do a word wrap that respects previous newlines.

    This is done by splitting on \n first and then wrapping each line individually.
    """
    lines = text.split("\n")
    new_lines = []
    for line in lines:
        # textwrap seems to remove empty lines, even with setting the whitespace
        # args to False, this check lets us preserve them.
        if line:
            new_lines.extend(
                textwrap.wrap(
                    line, width=width, replace_whitespace=False, drop_whitespace=False
                )
            )
        else:
            new_lines.append("")
    return "\n".join(map(str.strip, new_lines))


# Display the examples
old_col, new_col = st.columns(2)

with old_col:
    st.subheader("Old Text")
    # Creating a container sets the height of it, this forces a scroll wheel that
    # /only/ moves the text in this box. This makes it easy to scroll the two
    # examples independently and align related sections.
    with st.container(height=st.session_state.height):
        # Get the text from the list based on the id -> position mapping, not the
        # position of the cursor of the "next/prev" buttons.
        text = old[index[st.session_state.id].old]["text"]
        # Use st.text as `st.write` and `st.markdown` use markdown rules, removing
        # single newlines and only counting doubles as new paragraphs. Text lets us
        # keeep these newlines, but it the reason we needed our own wrap function.
        if to_wrap:
            st.text(wrap(text, st.session_state.width))
        else:
            st.text(text)

# Same comments as above, but we index into the list of /new/ examples.
with new_col:
    st.subheader("New Text")
    with st.container(height=st.session_state.height):
        text = new[index[st.session_state.id].new]["text"]
        if to_wrap:
            st.text(wrap(text, st.session_state.width))
        else:
            st.text(text)

# Show the metadata for the example. We don't expect it to change much so we just
# show it for the new version.
st.header("Metadata")
st.json(old[index[st.session_state.id].new]["metadata"], expanded=False)
