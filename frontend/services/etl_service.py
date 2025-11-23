import json
import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Callable, Generator

import requests

from frontend.settings import settings
from loguru import logger


@lru_cache(maxsize=1)
def get_api_base_url() -> str:
    base_url = settings.DEFUALT_API_BASE_URL.strip()
    if not base_url:
        raise ValueError("DEFUALT_API_BASE_URL environment variable is not set.")
    resolved = base_url.rstrip("/")
    logger.debug("Using backend API base URL {}", resolved)
    return resolved


def _build_url(path: str) -> str:
    url = f"{get_api_base_url()}{path}"
    logger.debug("Resolved backend endpoint {}", url)
    return url


def trigger_etl(sources: list[str]) -> dict[str, Any]:
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
    return _fetch_extraction_summary_once(dag_run_id)


@dataclass(slots=True)
class UploadedFilePayload:
    name: str
    content: bytes
    mime_type: str = "application/pdf"


def upload_source_file(payload: UploadedFilePayload) -> str:
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
