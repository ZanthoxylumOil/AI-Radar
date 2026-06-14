from __future__ import annotations

import hashlib
import html
import logging
import re
from calendar import timegm
from datetime import datetime, timedelta, timezone
from typing import Iterable

import feedparser
import requests

from .models import NewsItem

LOGGER = logging.getLogger(__name__)
TAG_RE = re.compile(r"<[^>]+>")
POLICY_KEYWORDS = (
    "人工智能",
    "ai",
    "大模型",
    "生成式",
    "算法",
    "算力",
    "数据",
    "数字经济",
    "数字金融",
    "金融科技",
    "量化",
    "程序化交易",
    "智能化",
)


def _clean(text: str) -> str:
    return " ".join(html.unescape(TAG_RE.sub(" ", text or "")).split())


def _published(entry: dict) -> datetime:
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if parsed:
        return datetime.fromtimestamp(timegm(parsed), tz=timezone.utc)
    return datetime.now(timezone.utc)


def _item_id(title: str, url: str) -> str:
    normalized = re.sub(r"\W+", "", title.lower())
    return hashlib.sha256(f"{normalized}|{url}".encode("utf-8")).hexdigest()[:24]


class FeedCollector:
    def __init__(self, timeout: int = 20, user_agent: str = "AI-Radar/1.0"):
        self.timeout = timeout
        self.user_agent = user_agent

    def collect(
        self, sources: Iterable[dict], max_items: int = 20, lookback_hours: int = 72
    ) -> list[NewsItem]:
        items: list[NewsItem] = []
        seen: set[str] = set()
        for source in sources:
            source_lookback = int(source.get("lookback_hours", lookback_hours))
            cutoff = datetime.now(timezone.utc) - timedelta(hours=source_lookback)
            source_limit = int(source.get("max_items", max_items))
            try:
                response = requests.get(
                    source["url"],
                    headers={"User-Agent": self.user_agent},
                    timeout=self.timeout,
                )
                response.raise_for_status()
                feed = feedparser.parse(response.content)
                for entry in feed.entries[:source_limit]:
                    title = _clean(entry.get("title", ""))
                    url = entry.get("link", "")
                    summary = _clean(
                        entry.get("summary", entry.get("description", ""))
                    )[:2000]
                    published = _published(entry)
                    if not title or not url or published < cutoff:
                        continue
                    keywords = source.get("include_keywords")
                    if keywords is None and source.get("category") in {
                        "policy",
                        "regulation",
                    }:
                        keywords = POLICY_KEYWORDS
                    searchable = f"{title} {summary}".lower()
                    if keywords and not any(
                        str(keyword).lower() in searchable for keyword in keywords
                    ):
                        continue
                    item = NewsItem(
                        id=_item_id(title, url),
                        source=source["name"],
                        title=title,
                        url=url,
                        summary=summary,
                        published_at=published.isoformat(timespec="seconds"),
                        region=source.get("region", "global"),
                        category=source.get("category", "news"),
                    )
                    if item.id not in seen:
                        seen.add(item.id)
                        items.append(item)
            except (requests.RequestException, KeyError) as exc:
                LOGGER.warning("Source %s failed: %s", source.get("name"), exc)
        return sorted(items, key=lambda item: item.published_at, reverse=True)