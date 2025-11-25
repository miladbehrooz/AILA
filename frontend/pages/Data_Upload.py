from typing import Any

import requests
import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile

from frontend.services.etl_service import (
    UploadedFilePayload,
    cancel_etl_run,
    fetch_extraction_summary,
    trigger_etl,
    upload_source_file,
    wait_for_dag_completion,
)
from frontend.state import source_fields
from frontend.utils.errors import show_technical_issue
from frontend.utils.text import human_join
from loguru import logger

ACTIVE_DAG_RUN_KEY = "active_dag_run_id"


def render_page() -> None:
    logger.debug("Rendering Data Upload page")
    st.title("Data Upload")
    st.caption(
        "Supported Sources (web articles, youtube videos, github repos, PDF files)."
    )

    source_fields.init_source_fields()
    st.session_state.setdefault(ACTIVE_DAG_RUN_KEY, None)
    _render_source_inputs()

    upload_col, cancel_col = st.columns([2.8, 1.2])
    with upload_col:
        if st.button("Upload", type="primary", use_container_width=True):
            logger.info(
                f"Upload button clicked with {len(source_fields.get_source_fields())} source field(s)",
            )
            _handle_submission()
    with cancel_col:
        if st.button("Cancel", type="secondary", use_container_width=True):
            _handle_cancel()


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
    logger.info("Handling data upload submission")
    sources, errors = _collect_sources()
    logger.debug(
        f"Collected {len(sources)} source(s) with { len(errors)} validation error(s)",
    )

    if not sources:
        logger.warning("Submission aborted because no sources were provided")
        st.error("Please provide at least one source.")
        return
    if errors:
        logger.warning(f"Submission blocked due to validation errors: {errors}")
        st.error(errors[0])
        return

    try:
        trigger_response = trigger_etl(sources)
    except requests.HTTPError as exc:
        detail = exc.response.text if exc.response is not None else str(exc)
        show_technical_issue(
            log_message=f"ETL trigger request failed: {detail}",
            exc=exc,
        )
        return
    except requests.RequestException as exc:
        show_technical_issue(
            log_message="Unable to reach backend API while triggering ETL run.",
            exc=exc,
        )
        return

    dag_run_id = trigger_response.get("dag_run_id")
    logger.info(f"Backend returned dag_run_id={ dag_run_id} for upload submission")
    summary_data: dict[str, Any] | None = None

    if dag_run_id:
        st.session_state[ACTIVE_DAG_RUN_KEY] = dag_run_id
        status_box = st.status(
            "Awaiting data upload status updates...",
            state="running",
            expanded=False,
        )

        def _update_state(state: str) -> None:
            status_box.update(
                label="Data upload is running...",
                state="running",
                expanded=False,
            )

        try:
            final_state = wait_for_dag_completion(dag_run_id, _update_state)
        except requests.RequestException as exc:
            logger.opt(exception=exc).error(
                "Unable to stream data upload status updates for dag_run_id={}",
                dag_run_id,
            )
            status_box.update(
                label=(
                    "We couldn't stream data upload status updates due to "
                    "a technical issue. Please try again later."
                ),
                state="error",
                expanded=False,
            )
            final_state = None
        else:
            if final_state == "success":
                status_box.update(
                    label="Data upload finished successfully.",
                    state="complete",
                    expanded=False,
                )
            elif final_state:
                status_box.update(
                    label=f"Data upload finished with state `{final_state}`.",
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
            show_technical_issue(
                log_message=(
                    f"HTTP error while retrieving extraction summary for "
                    f"dag_run_id={dag_run_id}: {detail}"
                ),
                exc=exc,
                level="warning",
            )
        except requests.RequestException as exc:
            show_technical_issue(
                log_message=(
                    f"Request error while contacting backend for extraction summary "
                    f"dag_run_id={dag_run_id}"
                ),
                exc=exc,
                level="warning",
            )
        finally:
            st.session_state[ACTIVE_DAG_RUN_KEY] = None
    else:
        logger.warning("Backend did not include dag_run_id for upload submission")
        st.info(
            "The backend did not return a DAG run identifier, "
            "so status monitoring and duplicate detection could not be performed."
        )

    if summary_data:
        logger.info(f"Rendering extraction summary for dag_run_id={dag_run_id}")
        _render_summary(summary_data)
    else:
        logger.info(f"Extraction summary not available for dag_run_id={dag_run_id}")
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


def _handle_cancel() -> None:
    dag_run_id = st.session_state.get(ACTIVE_DAG_RUN_KEY)
    if not dag_run_id:
        st.info("There is no active data upload to cancel.")
        return

    logger.info("Cancel button clicked for dag_run_id={}", dag_run_id)
    try:
        response = cancel_etl_run(dag_run_id)
    except requests.HTTPError as exc:
        detail = exc.response.text if exc.response is not None else str(exc)
        show_technical_issue(
            log_message=(
                f"Backend rejected ETL cancellation for dag_run_id={dag_run_id}: {detail}"
            ),
            exc=exc,
        )
        return
    except requests.RequestException as exc:
        show_technical_issue(
            log_message=(
                f"Unable to reach backend API while cancelling dag_run_id={dag_run_id}."
            ),
            exc=exc,
        )
        return

    st.session_state[ACTIVE_DAG_RUN_KEY] = None
    logger.info("ETL cancellation response for dag_run_id={}", dag_run_id)
    st.success("Cancellation requested successfully.")


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


if __name__ == "__main__":
    render_page()
