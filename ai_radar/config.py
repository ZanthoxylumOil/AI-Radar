from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    database_path: Path = Path(os.getenv("DATABASE_PATH", "data/ai_radar.db"))
    report_dir: Path = Path(os.getenv("REPORT_DIR", "reports"))
    sources_path: Path = Path(os.getenv("SOURCES_PATH", "config/sources.json"))
    max_items_per_source: int = _int("MAX_ITEMS_PER_SOURCE", 20)
    lookback_hours: int = _int("LOOKBACK_HOURS", 72)
    request_timeout: int = _int("REQUEST_TIMEOUT", 20)
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_base_url: str = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4.1-mini")
    llm_timeout: int = _int("LLM_TIMEOUT", 60)

    def prepare(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.report_dir.mkdir(parents=True, exist_ok=True)

    def load_sources(self) -> list[dict]:
        with self.sources_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)