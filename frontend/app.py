import json
import os
import time
import uuid
from pathlib import Path
from typing import Any, Callable

import requests
import streamlit as st
from dotenv import load_dotenv
from streamlit.runtime.uploaded_file_manager import UploadedFile


load_dotenv()


def list_to_str(items: list[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


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


def stream_etl_states(dag_run_id: str):
    url = f"{get_api_base_url()}/etl/stream-etl-status/{dag_run_id}"
    with requests.get(url, stream=True, timeout=60) as response:
        response.raise_for_status()
        for line in response.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data:"):
                continue
            payload = line.partition("data:")[2].strip()
            if not payload:
                continue
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                continue
            state = data.get("state")
            if state:
                yield state.lower()


def wait_for_dag_completion(
    dag_run_id: str, on_state_update: Callable[[str], None] | None = None
) -> str | None:
    try:
        for state in stream_etl_states(dag_run_id):
            if on_state_update:
                on_state_update(state)
            if state in {"success", "failed"}:
                return state
    except requests.RequestException:
        raise
    return None


def fetch_extraction_summary(
    dag_run_id: str, max_attempts: int = 10, delay_seconds: float = 3.0
) -> dict[str, Any] | None:
    url = f"{get_api_base_url()}/etl/extracted-sources/{dag_run_id}"
    for attempt in range(max_attempts):
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as exc:
            status_code = exc.response.status_code if exc.response else None
            if status_code == 404:
                if attempt < max_attempts - 1:
                    time.sleep(delay_seconds)
                    continue
                return None
            raise
        except requests.RequestException:
            if attempt < max_attempts - 1:
                time.sleep(delay_seconds)
                continue
            raise
    return None


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
    st.set_page_config(page_title="Source Upload", layout="centered")
    st.title("Source Upload")
    st.caption(
        "Upload Sources (web articles, youtube videos, github repos, PDF files)."
    )

    init_source_fields()

    for idx, field in enumerate(st.session_state.source_fields):
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

    submitted = st.button("Upload", type="primary", use_container_width=True)

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
            st.error("Please provide at least one source.")
        elif errors:
            st.error(errors[0])
        else:
            trigger_response: dict[str, Any] | None = None
            try:
                trigger_response = trigger_etl(sources)
            except requests.HTTPError as exc:
                detail = exc.response.text if exc.response is not None else str(exc)
                st.error(f"Request failed: {detail}")
            except requests.RequestException as exc:
                st.error(f"Unable to reach backend API: {exc}")

            if trigger_response is None:
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
                    st.warning(
                        f"Unable to contact backend for extraction summary: {exc}"
                    )
            else:
                st.info(
                    "The backend did not return a DAG run identifier, "
                    "so status monitoring and duplicate detection could not be performed."
                )

            if summary_data:
                if summary_data.get("new_sources"):
                    st.success(
                        f"{list_to_str(summary_data['new_sources'])} uploaded successfully."
                    )

                if summary_data.get("duplicate_sources"):
                    st.warning(
                        f"{list_to_str(summary_data['duplicate_sources']) } already exist."
                    )
                if summary_data.get("failed_sources"):
                    st.error(
                        f"{list_to_str(summary_data['failed_sources'])} failed to upload."
                    )

            else:
                st.info("Extraction summary is not available yet. ")


if __name__ == "__main__":
    render_app()
