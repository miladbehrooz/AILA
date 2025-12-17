import uuid

import streamlit as st

SourceField = dict[str, str]


def init_source_fields() -> None:
    """Initialize the session state list of source fields."""
    if "source_fields" not in st.session_state:
        st.session_state.source_fields = [{"id": str(uuid.uuid4()), "mode": "url"}]


def get_source_fields() -> list[SourceField]:
    """Return the list of source fields from session state.
    Returns:
        list[SourceField]: List of source field dictionaries.
    """
    init_source_fields()
    return st.session_state.source_fields


def add_source_field_at(index: int) -> None:
    """Insert a new source field after the provided index.
    Args:
        index (int): Index after which to insert the new field.
    """
    st.session_state.source_fields.insert(
        index + 1, {"id": str(uuid.uuid4()), "mode": "url"}
    )


def remove_source_field_at(index: int) -> None:
    """Remove a source field and clean up associated session state.
    Args:
        index (int): Index of the field to remove.
    """
    fields = st.session_state.source_fields
    if len(fields) == 1:
        return
    field = fields.pop(index)
    st.session_state.pop(f"source_{field['id']}", None)
    st.session_state.pop(f"file_{field['id']}", None)


def toggle_field_mode(field_id: str) -> None:
    """Flip a field between URL input mode and file upload mode.
    Args:
        field_id (str): Identifier of the source field to toggle.
    """
    for field in st.session_state.source_fields:
        if field["id"] == field_id:
            field["mode"] = "file" if field.get("mode") == "url" else "url"
            break


def remember_uploaded_file(stored_path: str, display_name: str) -> None:
    """Persist a mapping between stored file paths and display names.
    Args:
        stored_path (str): Path where the file is stored.
        display_name (str): Friendly name for display purposes.
    """
    uploaded_file_names = st.session_state.setdefault("uploaded_file_names", {})
    uploaded_file_names[stored_path] = display_name


def display_name_for_source(source: str) -> str:
    """Return the friendly name for a stored source path.
    Args:
        source (str): Stored source path.
    Returns:
        str: Friendly display name for the source.
    """
    uploaded_file_names = st.session_state.get("uploaded_file_names", {})
    return uploaded_file_names.get(source, source)


def display_names_for_sources(sources: list[str]) -> list[str]:
    """Return the friendly names for a list of stored source paths.
    Args:
        sources (list[str]): List of stored source paths.
    Returns:
        list[str]: List of friendly display names for the sources.
    """
    return [display_name_for_source(source) for source in sources]
