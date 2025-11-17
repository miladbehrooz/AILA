import uuid
from typing import Any

import streamlit as st


SourceField = dict[str, str]


def init_source_fields() -> None:
    if "source_fields" not in st.session_state:
        st.session_state.source_fields = [{"id": str(uuid.uuid4()), "mode": "url"}]


def get_source_fields() -> list[SourceField]:
    init_source_fields()
    return st.session_state.source_fields


def add_source_field_at(index: int) -> None:
    st.session_state.source_fields.insert(
        index + 1, {"id": str(uuid.uuid4()), "mode": "url"}
    )


def remove_source_field_at(index: int) -> None:
    fields = st.session_state.source_fields
    if len(fields) == 1:
        return
    field = fields.pop(index)
    st.session_state.pop(f"source_{field['id']}", None)
    st.session_state.pop(f"file_{field['id']}", None)


def toggle_field_mode(field_id: str) -> None:
    for field in st.session_state.source_fields:
        if field["id"] == field_id:
            field["mode"] = "file" if field.get("mode") == "url" else "url"
            break


def remember_uploaded_file(stored_path: str, display_name: str) -> None:
    uploaded_file_names = st.session_state.setdefault("uploaded_file_names", {})
    uploaded_file_names[stored_path] = display_name


def display_name_for_source(source: str) -> str:
    uploaded_file_names = st.session_state.get("uploaded_file_names", {})
    return uploaded_file_names.get(source, source)


def display_names_for_sources(sources: list[str]) -> list[str]:
    return [display_name_for_source(source) for source in sources]
