import json
import time
from collections.abc import Generator
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Callable

import requests
from loguru import logger

from frontend.settings import settings


@lru_cache(maxsize=1)
def get_api_base_url() -> str:
    """Return the sanitized base URL for the backend API.
    Returns:
        str: Backend API base URL without trailing slash.
    """
    base_url = settings.DEFUALT_API_BASE_URL.strip()
    if not base_url:
        raise ValueError("DEFUALT_API_BASE_URL environment variable is not set.")
    resolved = base_url.rstrip("/")
    logger.debug("Using backend API base URL {}", resolved)
    return resolved


def _build_url(path: str) -> str:
    """Compose a backend URL by appending the given path to the base.

    Args:
        path (str): API path, e.g. `/etl/runs`.

    Returns:
        str: Fully qualified URL.
    """
    url = f"{get_api_base_url()}{path}"
    logger.debug("Resolved backend endpoint {}", url)
    return url


def trigger_etl(sources: list[str]) -> dict[str, Any]:
    """Trigger the backend ETL run for the provided sources.

    Args:
        sources (list[str]): URLs or file paths to ingest.

    Returns:
        dict[str, Any]: Backend response describing the scheduled DAG run.
    """
    logger.info(f"Triggering ETL run for {len(sources)} source(s)")
    try:
        response = requests.post(
            _build_url("/etl/runs"),
            json={"sources": sources},
            timeout=60,
        )
        response.raise_for_status()
    except requests.RequestException:
        logger.exception(f"Failed to trigger ETL run for {len(sources)} source(s)")
        raise

    payload = response.json()
    logger.info(
        "ETL trigger accepted: dag_run_id={} ({} source(s))",
        payload.get("dag_run_id"),
        len(sources),
    )
    return payload


def stream_etl_states(dag_run_id: str) -> Generator[str, None, None]:
    """Yield state updates for the DAG run as they arrive.

    Args:
        dag_run_id (str): Identifier of the DAG run to watch.

    Yields:
        str: Lowercased Airflow state whenever it changes.
    """
    logger.info("Streaming ETL states for dag_run_id={}", dag_run_id)
    try:
        with requests.get(
            _build_url(f"/etl/runs/{dag_run_id}/status/stream"),
            stream=True,
            timeout=60,
        ) as response:
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
                    lowered_state = state.lower()
                    logger.debug(
                        "ETL state update for dag_run_id={}: {}",
                        dag_run_id,
                        lowered_state,
                    )
                    yield lowered_state
    except requests.RequestException:
        logger.exception(f"Unable to stream ETL states for dag_run_id={ dag_run_id}")
        raise
    finally:
        logger.info(f"Stopped streaming ETL states for dag_run_id={dag_run_id}")


def wait_for_dag_completion(
    dag_run_id: str, on_state_update: Callable[[str], None] | None = None
) -> str | None:
    """Block until the DAG run reaches a terminal state.

    Args:
        dag_run_id (str): Identifier of the DAG run to monitor.
        on_state_update (Callable[[str], None] | None): Optional callback invoked on
            every intermediate state.

    Returns:
        str | None: Final state when available, otherwise None if the stream ended.
    """
    logger.info("Waiting for DAG run {} to reach a terminal state", dag_run_id)
    for state in stream_etl_states(dag_run_id):
        logger.debug("DAG run {} reported state {}", dag_run_id, state)
        if on_state_update:
            on_state_update(state)
        if state in {"success", "failed"}:
            logger.info("DAG run {} finished with state {}", dag_run_id, state)
            return state

    logger.warning("State stream ended before completion for dag_run_id={}", dag_run_id)
    return None


def _fetch_extraction_summary_once(dag_run_id: str) -> dict[str, Any] | None:
    """Fetch the extraction summary exactly once.

    Args:
        dag_run_id (str): Identifier of the DAG run whose summary is requested.

    Returns:
        dict[str, Any] | None: Summary payload or None when still pending.
    """
    url = _build_url(f"/etl/runs/{dag_run_id}/extracted-sources")
    logger.debug("Fetching extraction summary from {}", url)
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        payload = response.json()
        logger.debug("Extraction summary payload loaded for dag_run_id={}", dag_run_id)
        return payload
    except requests.HTTPError as exc:
        status_code = exc.response.status_code if exc.response else None
        if status_code == 404:
            logger.info(
                "Extraction summary not ready for dag_run_id={} (404)",
                dag_run_id,
            )
            return None
        logger.exception(
            "Failed to fetch extraction summary for dag_run_id={} (status={})",
            dag_run_id,
            status_code,
        )
        raise


def fetch_extraction_summary(
    dag_run_id: str, max_attempts: int = 10, delay_seconds: float = 3.0
) -> dict[str, Any] | None:
    """Poll the backend until an extraction summary becomes available.

    Args:
        dag_run_id (str): Identifier of the DAG run whose summary is requested.
        max_attempts (int, optional): Maximum number of polling attempts.
        delay_seconds (float, optional): Delay between attempts in seconds.

    Returns:
        dict[str, Any] | None: Summary payload or None when attempts are exhausted.
    """
    logger.info(
        "Polling extraction summary for dag_run_id={} (attempts={}, delay={}s)",
        dag_run_id,
        max_attempts,
        delay_seconds,
    )
    for attempt in range(max_attempts):
        logger.debug(
            "Extraction summary poll attempt {} for dag_run_id={}",
            attempt + 1,
            dag_run_id,
        )
        try:
            result = _fetch_extraction_summary_once(dag_run_id)
            if result is not None:
                logger.info(
                    "Extraction summary ready for dag_run_id={} on attempt {}",
                    dag_run_id,
                    attempt + 1,
                )
                return result
            if attempt < max_attempts - 1:
                time.sleep(delay_seconds)
        except requests.HTTPError:
            raise
        except requests.RequestException:
            if attempt < max_attempts - 1:
                logger.warning(
                    "Request failed while polling dag_run_id={}, retrying (attempt {})",
                    dag_run_id,
                    attempt + 1,
                )
                time.sleep(delay_seconds)
                continue
            logger.exception(
                "Exhausted retries while fetching summary for dag_run_id={}",
                dag_run_id,
            )
            raise

    logger.warning(
        "Extraction summary unavailable after {} attempts for dag_run_id={}",
        max_attempts,
        dag_run_id,
    )
    return None


def fetch_extraction_summary_once(dag_run_id: str) -> dict[str, Any] | None:
    """Public proxy for a single extraction summary request.

    Args:
        dag_run_id (str): Identifier of the DAG run whose summary is requested.

    Returns:
        dict[str, Any] | None: Summary payload or None when still pending.
    """
    return _fetch_extraction_summary_once(dag_run_id)


@dataclass(slots=True)
class UploadedFilePayload:
    """Payload used when uploading a file to the backend API."""

    name: str
    content: bytes
    mime_type: str = "application/pdf"


def upload_source_file(payload: UploadedFilePayload) -> str:
    """Upload a local file to the backend and return its stored path.

    Args:
        payload (UploadedFilePayload): Payload containing file bytes and metadata.

    Returns:
        str: Relative path assigned by the backend.
    """
    logger.info(
        "Uploading source file '{}' ({} bytes)",
        payload.name,
        len(payload.content),
    )
    files = {
        "file": (
            payload.name,
            payload.content,
            payload.mime_type or "application/pdf",
        )
    }
    try:
        response = requests.post(
            _build_url("/etl/files"),
            files=files,
            timeout=60,
        )
        response.raise_for_status()
    except requests.RequestException:
        logger.exception("Failed to upload source file '{}'", payload.name)
        raise

    stored_path = response.json().get("stored_path")
    if not stored_path:
        logger.error(
            "Backend did not return stored_path for uploaded file '{}'", payload.name
        )
        raise ValueError("Backend did not return stored_path for uploaded file.")

    logger.info(
        "File '{}' uploaded successfully and stored at {}",
        payload.name,
        stored_path,
    )
    return stored_path


def list_etl_runs(limit: int = 25, offset: int = 0) -> dict[str, Any]:
    """List ETL runs using the backend API.

    Args:
        limit (int, optional): Maximum number of runs to fetch. Defaults to 25.
        offset (int, optional): Pagination offset. Defaults to 0.

    Returns:
        dict[str, Any]: Backend response containing the paginated runs.
    """
    logger.debug("Listing ETL runs with limit={} offset={}", limit, offset)
    try:
        response = requests.get(
            _build_url("/etl/runs"),
            params={"limit": limit, "offset": offset},
            timeout=60,
        )
        response.raise_for_status()
    except requests.RequestException:
        logger.exception(
            "Unable to list ETL runs with limit={} offset={}", limit, offset
        )
        raise

    payload = response.json()
    logger.info(
        "Fetched {} ETL run(s) (limit={} offset={})",
        len(payload.get("dag_runs", [])),
        limit,
        offset,
    )
    return payload


def get_etl_run(dag_run_id: str) -> dict[str, Any]:
    """Fetch metadata for a specific ETL run.

    Args:
        dag_run_id (str): DAG run identifier to retrieve.

    Returns:
        dict[str, Any]: Backend response describing the run.
    """
    logger.debug("Fetching ETL run dag_run_id={}", dag_run_id)
    try:
        response = requests.get(
            _build_url(f"/etl/runs/{dag_run_id}"),
            timeout=60,
        )
        response.raise_for_status()
    except requests.RequestException:
        logger.exception("Unable to fetch ETL run dag_run_id={}", dag_run_id)
        raise

    payload = response.json()
    logger.info("Fetched ETL run metadata for dag_run_id={}", dag_run_id)
    return payload


def cancel_etl_run(dag_run_id: str) -> dict[str, Any]:
    """Request cancellation for the provided ETL run.

    Args:
        dag_run_id (str): Identifier of the DAG run to cancel.

    Returns:
        dict[str, Any]: Backend response acknowledging the cancellation.
    """
    logger.info("Requesting cancellation for dag_run_id={}", dag_run_id)
    try:
        response = requests.delete(
            _build_url(f"/etl/runs/{dag_run_id}"),
            timeout=60,
        )
        response.raise_for_status()
    except requests.RequestException:
        logger.exception("Failed to cancel ETL run dag_run_id={}", dag_run_id)
        raise

    payload = response.json()
    logger.info(
        "Cancellation acknowledged for dag_run_id={} (dag_id={})",
        dag_run_id,
        payload.get("dag_id"),
    )
    return payload
