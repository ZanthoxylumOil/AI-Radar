from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class NewsItem:
    source: str
    title: str
    url: str
    summary: str
    published_at: str
    region: str = "global"
    category: str = "news"
    id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Analysis:
    item_id: str
    relevance_score: int
    sentiment: str
    event_type: str
    securities_impact: str
    quant_impact: str
    opportunities: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    affected_assets: list[str] = field(default_factory=list)
    time_horizon: str = "中期"
    confidence: float = 0.5
    model: str = "rule-engine"
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)