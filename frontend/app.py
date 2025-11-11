import os
import uuid
from typing import Any

import requests
import streamlit as st
from dotenv import load_dotenv


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
        st.session_state.source_fields = [{"id": str(uuid.uuid4())}]


def add_source_field_at(index: int) -> None:
    st.session_state.source_fields.insert(index + 1, {"id": str(uuid.uuid4())})


def remove_source_field_at(index: int) -> None:
    fields = st.session_state.source_fields
    if len(fields) == 1:
        return
    field = fields.pop(index)
    st.session_state.pop(field["id"], None)


def render_app() -> None:
    st.set_page_config(page_title="LAIA ETL Trigger", layout="centered")
    st.title("LAIA ETL Trigger")
    st.caption("Trigger the ETL pipeline for one or more sources.")

    init_source_fields()

    for idx, field in enumerate(st.session_state.source_fields):
        input_col, add_col, remove_col = st.columns([6, 1, 1])
        input_col.text_input(
            f"Source {idx + 1}",
            placeholder="https://example.com/article or /path/to/local/file",
            key=field["id"],
        )
        add_col.button(
            "add",
            key=f"add_{field['id']}",
            on_click=add_source_field_at,
            args=(idx,),
            use_container_width=True,
        )
        remove_col.button(
            "remove",
            key=f"remove_{field['id']}",
            on_click=remove_source_field_at,
            args=(idx,),
            disabled=len(st.session_state.source_fields) == 1,
            use_container_width=True,
        )

    submitted = st.button("Trigger ETL", type="primary", use_container_width=True)

    if submitted:
        sources = [
            st.session_state.get(field["id"], "").strip()
            for field in st.session_state.source_fields
            if st.session_state.get(field["id"], "").strip()
        ]
        if not sources:
            st.error(
                "Please provide at least one source before triggering the pipeline."
            )
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
