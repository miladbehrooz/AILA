from typing import Any

import requests
import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile

from frontend.services.etl_service import (
    UploadedFilePayload,
    fetch_extraction_summary,
    trigger_etl,
    upload_source_file,
    wait_for_dag_completion,
)
from frontend.state import source_fields
from frontend.utils.text import human_join


def render_page() -> None:
    st.title("Source Upload")
    st.caption(
        "Upload Sources (web articles, youtube videos, github repos, PDF files)."
    )

    source_fields.init_source_fields()
    _render_source_inputs()

    if st.button("Upload", type="primary", use_container_width=True):
        _handle_submission()


def _render_source_inputs() -> None:
    fields = source_fields.get_source_fields()
    for idx, field in enumerate(fields):
        field_id = field["id"]
        mode = field.get("mode", "url")
        input_col, upload_col, add_col, remove_col = st.columns([5.8, 0.8, 0.8, 0.8])

        if mode == "url":
            input_col.text_input(
                "Source URL (web article / YouTube / GitHub)",
                placeholder="https://example.com/article",
                key=f"source_{field_id}",
                label_visibility="collapsed",
            )
        else:
            input_col.file_uploader(
                "Upload PDF file",
                key=f"file_{field_id}",
                label_visibility="collapsed",
            )

        upload_col.button(
            "📁" if mode == "url" else "🔗",
            key=f"toggle_{field_id}",
            on_click=source_fields.toggle_field_mode,
            args=(field_id,),
            use_container_width=True,
        )

        add_col.button(
            "➕",
            key=f"add_{field_id}",
            on_click=source_fields.add_source_field_at,
            args=(idx,),
            use_container_width=True,
        )

        remove_col.button(
            "➖",
            key=f"remove_{field_id}",
            on_click=source_fields.remove_source_field_at,
            args=(idx,),
            disabled=len(fields) == 1,
            use_container_width=True,
        )


def _handle_submission() -> None:
    sources, errors = _collect_sources()

    if not sources:
        st.error("Please provide at least one source.")
        return
    if errors:
        st.error(errors[0])
        return

    try:
        trigger_response = trigger_etl(sources)
    except requests.HTTPError as exc:
        detail = exc.response.text if exc.response is not None else str(exc)
        st.error(f"Request failed: {detail}")
        return
    except requests.RequestException as exc:
        st.error(f"Unable to reach backend API: {exc}")
        return

    dag_run_id = trigger_response.get("dag_run_id")
    summary_data: dict[str, Any] | None = None

    if dag_run_id:
        status_box = st.status(
            "Awaiting source upload status updates...",
            state="running",
            expanded=False,
        )

        def _update_state(state: str) -> None:
            status_box.update(
                label="Source upload is running...",
                state="running",
                expanded=False,
            )

        try:
            final_state = wait_for_dag_completion(dag_run_id, _update_state)
        except requests.RequestException as exc:
            status_box.update(
                label=f"Unable to stream source upload status updates: {exc}",
                state="error",
                expanded=False,
            )
            final_state = None
        else:
            if final_state == "success":
                status_box.update(
                    label="Source upload finished successfully.",
                    state="complete",
                    expanded=False,
                )
            elif final_state:
                status_box.update(
                    label=f"Source upload finished with state `{final_state}`.",
                    state="error",
                    expanded=False,
                )
            else:
                status_box.update(
                    label=(
                        "Status stream ended before a final state was reported. "
                        "Check Airflow for the latest status."
                    ),
                    state="error",
                    expanded=False,
                )

        try:
            summary_data = fetch_extraction_summary(
                dag_run_id, max_attempts=20, delay_seconds=3
            )
        except requests.HTTPError as exc:
            detail = exc.response.text if exc.response is not None else str(exc)
            st.warning(
                "Unable to retrieve extraction summary "
                f"for DAG run {dag_run_id}: {detail}"
            )
        except requests.RequestException as exc:
            st.warning(f"Unable to contact backend for extraction summary: {exc}")
    else:
        st.info(
            "The backend did not return a DAG run identifier, "
            "so status monitoring and duplicate detection could not be performed."
        )

    if summary_data:
        _render_summary(summary_data)
    else:
        st.info("Extraction summary is not available yet.")


def _collect_sources() -> tuple[list[str], list[str]]:
    collected_sources: list[str] = []
    errors: list[str] = []

    for field in source_fields.get_source_fields():
        field_id = field["id"]
        mode = field.get("mode", "url")

        if mode == "url":
            value = st.session_state.get(f"source_{field_id}", "").strip()
            if value:
                collected_sources.append(value)
        else:
            uploaded: UploadedFile | None = st.session_state.get(f"file_{field_id}")
            if uploaded:
                payload = UploadedFilePayload(
                    name=uploaded.name,
                    content=uploaded.getvalue(),
                    mime_type=uploaded.type or "application/pdf",
                )
                stored_path = upload_source_file(payload)
                source_fields.remember_uploaded_file(stored_path, uploaded.name)
                collected_sources.append(stored_path)
            else:
                errors.append("Please select a file for all upload inputs.")

    return collected_sources, errors


def _render_summary(summary_data: dict[str, Any]) -> None:
    if summary_data.get("new_sources"):
        new_sources = source_fields.display_names_for_sources(
            summary_data["new_sources"]
        )
        st.success(f"{human_join(new_sources)} uploaded successfully.")

    if summary_data.get("duplicate_sources"):
        duplicate_sources = source_fields.display_names_for_sources(
            summary_data["duplicate_sources"]
        )
        st.warning(f"{human_join(duplicate_sources)} already exist.")

    if summary_data.get("failed_sources"):
        failed_sources = source_fields.display_names_for_sources(
            summary_data["failed_sources"]
        )
        st.error(f"{human_join(failed_sources)} failed to upload.")
