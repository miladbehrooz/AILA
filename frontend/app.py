import os
from typing import Any
import requests
import streamlit as st
from load_dotenv import load_dotenv


def get_api_base_url() -> str:
    load_dotenv()
    api_url = os.getenv("DEFUALT_API_BASE_URL")
    if api_url is None:
        raise ValueError("DEFUALT_API_BASE_URL environment variable is not set.")
    return api_url


def trigger_etl(source: str) -> dict[str, Any]:
    response = requests.post(
        f"{get_api_base_url()}/etl/trigger",
        json={"sources": [source]},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def render_app() -> None:
    st.set_page_config(page_title="LAIA ETL Trigger", layout="centered")
    st.title("LAIA ETL Trigger")
    st.caption("Trigger the ETL pipeline for a given source.")

    with st.form("etl_trigger_form"):
        source = st.text_input(
            "Source URL or File Path",
            placeholder="https://example.com/article or /path/to/local/file",
        ).strip()

        submitted = st.form_submit_button("Trigger ETL", use_container_width=True)

        if submitted:
            if not source:
                st.error("Please provide a source before triggering the pipeline.")
            else:
                with st.spinner("Triggering ETL..."):
                    try:
                        data = trigger_etl(source)
                        st.success("ETL pipeline triggered successfully.")
                        st.json(data)
                    except requests.HTTPError as exc:
                        detail = (
                            exc.response.text if exc.response is not None else str(exc)
                        )
                        st.error(f"Request failed: {detail}")
                    except requests.RequestException as exc:
                        st.error(f"Unable to reach backend API: {exc}")


if __name__ == "__main__":
    render_app()
