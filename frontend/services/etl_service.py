from __future__ import annotations

import json
import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Callable, Generator

import requests

from frontend.settings.settings import settings


@lru_cache(maxsize=1)
def get_api_base_url() -> str:
    base_url = settings.DEFUALT_API_BASE_URL.strip()
    if not base_url:
        raise ValueError("DEFUALT_API_BASE_URL environment variable is not set.")
    return base_url.rstrip("/")


def _build_url(path: str) -> str:
    return f"{get_api_base_url()}{path}"


def trigger_etl(sources: list[str]) -> dict[str, Any]:
    response = requests.post(
        _build_url("/etl/trigger"),
        json={"sources": sources},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def stream_etl_states(dag_run_id: str) -> Generator[str, None, None]:
    with requests.get(
        _build_url(f"/etl/stream-etl-status/{dag_run_id}"), stream=True, timeout=60
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
                yield state.lower()


def wait_for_dag_completion(
    dag_run_id: str, on_state_update: Callable[[str], None] | None = None
) -> str | None:
    for state in stream_etl_states(dag_run_id):
        if on_state_update:
            on_state_update(state)
        if state in {"success", "failed"}:
            return state
    return None


def fetch_extraction_summary(
    dag_run_id: str, max_attempts: int = 10, delay_seconds: float = 3.0
) -> dict[str, Any] | None:
    url = _build_url(f"/etl/extracted-sources/{dag_run_id}")
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


@dataclass(slots=True)
class UploadedFilePayload:
    name: str
    content: bytes
    mime_type: str = "application/pdf"


def upload_source_file(payload: UploadedFilePayload) -> str:
    files = {
        "file": (
            payload.name,
            payload.content,
            payload.mime_type or "application/pdf",
        )
    }
    response = requests.post(
        _build_url("/etl/upload-file"),
        files=files,
        timeout=60,
    )
    response.raise_for_status()
    stored_path = response.json().get("stored_path")
    if not stored_path:
        raise ValueError("Backend did not return stored_path for uploaded file.")
    return stored_path
