from datetime import datetime
from typing import Any

import requests
import streamlit as st

from frontend.services import etl_service


def render_page() -> None:
    st.title("Upload Dashboard")
    st.caption("Review historical file-upload sessions and their ETL outcomes.")

    controls_col, page_col = st.columns([1, 1])
    limit = controls_col.selectbox("Rows per page", options=[10, 25, 50, 100], index=1)
    page_value = page_col.number_input(
        "Page", min_value=1, value=1, step=1, format="%d"
    )
    page = int(page_value)
    offset = (page - 1) * limit

    try:
        with st.spinner("Loading ETL runs..."):
            runs_payload = etl_service.list_etl_runs(limit=limit, offset=offset)
    except requests.RequestException as exc:
        st.error(f"Unable to load ETL runs: {exc}")
        return

    runs: list[dict[str, Any]] = runs_payload.get("dag_runs", [])
    total_entries = runs_payload.get("total_entries")

    selected_run = _render_runs_table(runs, limit, offset, total_entries)

    if selected_run is None:
        return

    _render_run_details(selected_run)


def _render_runs_table(
    runs: list[dict[str, Any]], limit: int, offset: int, total_entries: Any
) -> dict[str, Any] | None:
    st.subheader("Recent runs")
    if total_entries is not None:
        st.caption(
            f"Showing runs {offset + 1}–{offset + len(runs)} of {total_entries}."
        )

    if not runs:
        st.info("No ETL runs were found. Upload a source to trigger a DAG run.")
        return None

    data = []
    for index, run in enumerate(runs):
        row_number = offset + index + 1
        run["_row_number"] = row_number
        data.append(
            {
                "Run #": row_number,
                "State": (run.get("state") or "unknown").capitalize(),
                "Execution Date": _format_timestamp(run.get("execution_date")),
                "Started": _format_timestamp(run.get("start_date")),
                "Ended": _format_timestamp(run.get("end_date")),
            }
        )

    table_event = st.dataframe(
        data,
        use_container_width=True,
        hide_index=True,
        selection_mode="single-row",
        key="upload_dashboard_runs_table",
        on_select="rerun",
    )

    selected_index = _extract_selected_row(table_event)
    if selected_index is None and runs:
        selected_index = 0

    return runs[selected_index] if selected_index is not None else None


def _render_run_details(run: dict[str, Any]) -> None:
    st.subheader("Run details")
    metadata_cols = st.columns(3)
    metadata_cols[0].metric("Run #", run.get("_row_number", "-"), delta=None)
    metadata_cols[1].metric("State", (run.get("state") or "unknown").capitalize())
    metadata_cols[2].metric("Triggered", _format_timestamp(run.get("start_date")))
    st.caption(f"Airflow DAG run ID: {run.get('dag_run_id') or '-'}")

    summary_placeholder = st.container()
    with summary_placeholder:
        try:
            summary = etl_service.fetch_extraction_summary_once(
                run.get("dag_run_id", "")
            )
        except requests.RequestException as exc:
            st.error(f"Unable to load extraction summary: {exc}")
            return

        if summary is None:
            st.info(
                "Extraction summary is not available yet. The DAG may still be in progress, or the summary has not been stored."
            )
            return

        _render_summary(summary)


def _render_summary(summary: dict[str, Any]) -> None:
    counts_col1, counts_col2, counts_col3 = st.columns(3)
    counts_col1.metric("New sources", len(summary.get("new_sources", [])))
    counts_col2.metric("Duplicates", len(summary.get("duplicate_sources", [])))
    counts_col3.metric("Failed", len(summary.get("failed_sources", [])))

    _render_source_list("New sources", summary.get("new_sources", []), "success")
    _render_source_list(
        "Duplicates detected", summary.get("duplicate_sources", []), "warning"
    )
    _render_source_list("Failed uploads", summary.get("failed_sources", []), "error")


def _render_source_list(label: str, items: list[str], level: str) -> None:
    if not items:
        return
    message = "\n".join(f"• {item}" for item in items)
    if level == "success":
        st.success(f"{label}:\n{message}")
    elif level == "warning":
        st.warning(f"{label}:\n{message}")
    else:
        st.error(f"{label}:\n{message}")


def _format_timestamp(value: Any) -> str:
    if not value or not isinstance(value, str):
        return "-"
    value = value.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return value
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _extract_selected_row(table_event: Any) -> int | None:
    selection = getattr(table_event, "selection", None)
    if selection is None:
        return None

    rows = None
    if isinstance(selection, dict):
        rows = selection.get("rows")
    else:
        rows = getattr(selection, "rows", None)
        if rows is None and hasattr(selection, "__dict__"):
            rows = selection.__dict__.get("rows")

    if not rows:
        return None

    try:
        return int(rows[0])
    except (TypeError, ValueError, IndexError):
        return None
