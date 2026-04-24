import math

import streamlit as st

from pdf_studio.canvas import THUMBNAIL_SCALE

CANVAS_PAGE_SIZE = 12


def ensure_session_state():
    defaults = {
        "documents": {},
        "page_items": [],
        "selected_page_ids": set(),
        "uploader_key": 0,
        "insert_position": 0,
        "canvas_page": 1,
        "output_pdf_bytes": None,
        "output_pdf_meta": None,
        "export_filename": "edited_output.pdf",
        "compression_profile": "balanced",
        "notices": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def invalidate_output():
    st.session_state.output_pdf_bytes = None
    st.session_state.output_pdf_meta = None


def refresh_uploader():
    st.session_state.uploader_key += 1


def set_notices(notices: list):
    st.session_state.notices = notices


def prune_unused_documents():
    active_ids = {p["document_id"] for p in st.session_state.page_items}
    st.session_state.documents = {
        doc_id: doc
        for doc_id, doc in st.session_state.documents.items()
        if doc_id in active_ids
    }


def clear_selection():
    for page_id in list(st.session_state.selected_page_ids):
        widget_key = f"select_{page_id}"
        if widget_key in st.session_state:
            st.session_state[widget_key] = False
    st.session_state.selected_page_ids = set()


def select_page_ids(page_ids):
    for page_id in page_ids:
        widget_key = f"select_{page_id}"
        if widget_key in st.session_state:
            st.session_state[widget_key] = True
    st.session_state.selected_page_ids.update(page_ids)


def hydrate_selection_from_widgets():
    selected = set(st.session_state.selected_page_ids)
    current_ids = {p["id"] for p in st.session_state.page_items}

    for page in st.session_state.page_items:
        widget_key = f"select_{page['id']}"
        if widget_key not in st.session_state:
            continue
        if st.session_state[widget_key]:
            selected.add(page["id"])
        else:
            selected.discard(page["id"])

    st.session_state.selected_page_ids = {pid for pid in selected if pid in current_ids}


def clamp_editor_state():
    total = len(st.session_state.page_items)
    current_ids = {p["id"] for p in st.session_state.page_items}
    st.session_state.selected_page_ids = {
        pid for pid in st.session_state.selected_page_ids if pid in current_ids
    }

    st.session_state.insert_position = max(
        0, min(st.session_state.insert_position, total)
    )

    max_canvas_page = max(1, math.ceil(total / CANVAS_PAGE_SIZE)) if total else 1
    st.session_state.canvas_page = max(
        1, min(st.session_state.canvas_page, max_canvas_page)
    )



def jump_canvas_to_index(index: int):
    st.session_state.canvas_page = max(1, (index // CANVAS_PAGE_SIZE) + 1)


def set_insert_position(position: int):
    st.session_state.insert_position = position
    clamp_editor_state()
