from datetime import datetime
from typing import Any

import pandas as pd
import requests
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

from frontend.services import etl_service

_SESSION_SELECTED_RUN = "upload_dashboard_selected_run"


def render_page() -> None:
    st.title("Data Upload Dashboard")
    st.caption("Review historical data upload sessions and their outcomes.")

    if "runs_table_limit" not in st.session_state:
        st.session_state["runs_table_limit"] = 25
    if "runs_table_page" not in st.session_state:
        st.session_state["runs_table_page"] = 1

    limit = st.session_state["runs_table_limit"]
    page = st.session_state["runs_table_page"]
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
        _render_table_controls(limit, page, total_entries)
        return

    _render_table_controls(limit, page, total_entries)
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

    data: list[dict[str, Any]] = []
    for index, run in enumerate(runs):
        if total_entries is not None:
            row_number = total_entries - (offset + index)
        else:
            row_number = offset + index + 1
        run["_row_number"] = row_number
        summary = _get_cached_summary(run.get("dag_run_id", ""))
        new_count, duplicate_count, failed_count = _summary_counts(summary)
        summary_text = _format_summary_counts(new_count, duplicate_count, failed_count)
        data.append(
            {
                "Run ID": row_number,
                "State": (run.get("state") or "unknown").capitalize(),
                "Execution Date": _format_timestamp(run.get("execution_date")),
                "Started": _format_timestamp(run.get("start_date")),
                "Ended": _format_timestamp(run.get("end_date")),
                "Run Summary": summary_text,
            }
        )

    data.sort(key=lambda row: row["Run ID"], reverse=True)
    table_df = pd.DataFrame(data)
    grid_builder = GridOptionsBuilder.from_dataframe(table_df)
    grid_builder.configure_selection("single", use_checkbox=False)
    grid_builder.configure_column("Run ID", width=90)
    grid_builder.configure_column("State", width=140)
    grid_builder.configure_column("Execution Date", width=200)
    grid_builder.configure_column("Started", width=200)
    grid_builder.configure_column("Ended", width=200)
    grid_builder.configure_column("Run Summary", width=260)
    grid_builder.configure_grid_options(domLayout="normal")
    grid_options = grid_builder.build()

    grid_response = AgGrid(
        table_df,
        gridOptions=grid_options,
        height=400,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        fit_columns_on_grid_load=True,
        theme="streamlit",
        key=f"upload_dashboard_runs_table_{offset}_{limit}",
    )

    selected_rows = grid_response.get("selected_rows")
    if selected_rows is None:
        selected_records: list[dict[str, Any]] = []
    elif isinstance(selected_rows, pd.DataFrame):
        selected_records = selected_rows.to_dict("records")
    elif isinstance(selected_rows, list):
        selected_records = selected_rows
    else:
        selected_records = [selected_rows]

    page_run_numbers = [row["Run ID"] for row in data]

    if selected_records:
        selected_run_number = selected_records[0].get("Run ID")
        if selected_run_number is not None:
            st.session_state[_SESSION_SELECTED_RUN] = selected_run_number
    else:
        selected_run_number = st.session_state.get(_SESSION_SELECTED_RUN)
        if selected_run_number not in page_run_numbers:
            selected_run_number = None

        if selected_run_number is None and page_run_numbers:
            selected_run_number = page_run_numbers[0]
            st.session_state[_SESSION_SELECTED_RUN] = selected_run_number

    final_run_number = st.session_state.get(_SESSION_SELECTED_RUN)
    return _find_run_by_number(runs, final_run_number)


def _render_run_details(run: dict[str, Any]) -> None:
    st.subheader("Run details")
    metadata_cols = st.columns(3)
    metadata_cols[0].metric("Run ID", run.get("_row_number", "-"), delta=None)
    metadata_cols[1].metric("State", (run.get("state") or "unknown").capitalize())
    metadata_cols[2].metric("Triggered", _format_timestamp(run.get("start_date")))

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
        st.caption(f"Airflow DAG run ID: {run.get('dag_run_id') or '-'}")


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


def _render_table_controls(limit: int, page: int, total_entries: Any) -> None:

    with st.container(border=False):
        control_cols = st.columns([1, 1, 1, 0.8, 1, 1, 1, 1])
        per_page_options = [10, 25, 50, 100]
        if limit not in per_page_options:
            per_page_options.append(limit)
            per_page_options.sort()

        new_limit = control_cols[3].selectbox(
            "Rows per page",
            options=per_page_options,
            index=per_page_options.index(limit),
        )

        max_page = (
            max(1, (total_entries + new_limit - 1) // new_limit)
            if (total_entries is not None and total_entries > 0)
            else page
        )

        new_page_value = control_cols[4].number_input(
            "Go to page",
            min_value=1,
            value=min(page, max_page),
            max_value=max_page,
            step=1,
        )
        target_page = int(new_page_value)

    if (
        target_page != st.session_state["runs_table_page"]
        or new_limit != st.session_state["runs_table_limit"]
    ):
        st.session_state["runs_table_page"] = target_page
        st.session_state["runs_table_limit"] = new_limit
        st.rerun()


@st.cache_data(show_spinner=False, ttl=120)
def _get_cached_summary(dag_run_id: str) -> dict[str, Any] | None:
    if not dag_run_id:
        return None
    try:
        return etl_service.fetch_extraction_summary_once(dag_run_id)
    except requests.RequestException:
        return None


def _summary_counts(summary: dict[str, Any] | None) -> tuple[str, str, str]:
    if not summary:
        return "-", "-", "-"
    return (
        str(len(summary.get("new_sources", []))),
        str(len(summary.get("duplicate_sources", []))),
        str(len(summary.get("failed_sources", []))),
    )


def _format_summary_counts(
    new_count: str, duplicate_count: str, failed_count: str
) -> str:
    return f"New: {new_count} | Duplicates: {duplicate_count} | Failed: {failed_count}"


def _find_run_by_number(
    runs: list[dict[str, Any]], row_number: Any
) -> dict[str, Any] | None:
    if row_number is None:
        return None

    for run in runs:
        if run.get("_row_number") == row_number:
            return run
    return None


def _format_timestamp(value: Any) -> str:
    if not value or not isinstance(value, str):
        return "-"
    value = value.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return value
    return dt.strftime("%Y-%m-%d %H:%M:%S")
