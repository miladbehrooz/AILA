import os
import uuid
from pathlib import Path
from typing import Any
import requests
import streamlit as st
from dotenv import load_dotenv
from streamlit.runtime.uploaded_file_manager import UploadedFile


load_dotenv()


def get_api_base_url() -> str:
    api_url = os.getenv("DEFUALT_API_BASE_URL", "").strip()
    if not api_url:
        raise ValueError("DEFUALT_API_BASE_URL environment variable is not set.")
    return api_url.rstrip("/")


def trigger_etl(sources: list[str]) -> dict[str, Any]:
    response = requests.post(
        f"{get_api_base_url()}/etl/trigger",
        json={"sources": sources},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def init_source_fields() -> None:
    if "source_fields" not in st.session_state:
        st.session_state.source_fields = [{"id": str(uuid.uuid4()), "mode": "url"}]


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


def persist_uploaded_file(uploaded: UploadedFile) -> str:
    uploads_dir = Path("frontend/uploads")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    destination = uploads_dir / f"{uuid.uuid4()}_{uploaded.name}"
    with destination.open("wb") as fh:
        fh.write(uploaded.getbuffer())
    return str(destination.resolve())


def render_app() -> None:
    st.set_page_config(page_title="LAIA ETL Trigger", layout="centered")
    st.title("LAIA ETL Trigger")
    st.caption("Trigger the ETL pipeline for one or more sources.")

    init_source_fields()

    for idx, field in enumerate(st.session_state.source_fields):
        field_id = field["id"]
        mode = field.get("mode", "url")

        input_col, upload_col, add_col, remove_col = st.columns([6, 1.3, 1, 1])
        if mode == "url":
            input_col.text_input(
                f"Source {idx + 1}",
                placeholder="https://example.com/article",
                key=f"source_{field_id}",
            )
        else:
            input_col.file_uploader(
                f"Upload File {idx + 1}",
                key=f"file_{field_id}",
            )

        upload_col.button(
            "📁" if mode == "url" else "🔗",
            key=f"toggle_{field_id}",
            on_click=toggle_field_mode,
            args=(field_id,),
            use_container_width=True,
        )

        add_col.button(
            "➕",
            key=f"add_{field_id}",
            on_click=add_source_field_at,
            args=(idx,),
            use_container_width=True,
        )
        remove_col.button(
            "➖",
            key=f"remove_{field_id}",
            on_click=remove_source_field_at,
            args=(idx,),
            disabled=len(st.session_state.source_fields) == 1,
            use_container_width=True,
        )

    submitted = st.button("Trigger ETL", type="primary", use_container_width=True)

    if submitted:
        sources: list[str] = []
        errors: list[str] = []

        for field in st.session_state.source_fields:
            field_id = field["id"]
            mode = field.get("mode", "url")

            if mode == "url":
                value = st.session_state.get(f"source_{field_id}", "").strip()
                if value:
                    sources.append(value)
            else:
                uploaded = st.session_state.get(f"file_{field_id}")
                if uploaded:
                    saved_path = persist_uploaded_file(uploaded)
                    sources.append(saved_path)
                else:
                    errors.append("Please select a file for all upload inputs.")

        if not sources:
            st.error(
                "Please provide at least one source before triggering the pipeline."
            )
        elif errors:
            st.error(errors[0])
        else:
            with st.spinner("Triggering ETL..."):
                try:
                    data = trigger_etl(sources)
                    st.success("ETL pipeline triggered successfully.")
                    st.json(data)
                except requests.HTTPError as exc:
                    detail = exc.response.text if exc.response is not None else str(exc)
                    st.error(f"Request failed: {detail}")
                except requests.RequestException as exc:
                    st.error(f"Unable to reach backend API: {exc}")


if __name__ == "__main__":
    render_app()
