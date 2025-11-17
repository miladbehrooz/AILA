from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env", override=False)


@dataclass(frozen=True, slots=True)
class Settings:
    DEFUALT_API_BASE_URL: str = "http://localhost:8000/"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    base_url = os.getenv("DEFUALT_API_BASE_URL", Settings.DEFUALT_API_BASE_URL)
    return Settings(DEFUALT_API_BASE_URL=base_url)
