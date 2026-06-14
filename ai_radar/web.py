from __future__ import annotations

from datetime import datetime, timedelta, timezone

from flask import Flask, jsonify, redirect, render_template, request, url_for

from .config import Settings
from .pipeline import RadarPipeline
from .storage import Repository

DATE_RANGES = (
    (0, "全部时间"),
    (30, "一月内"),
    (15, "半月内"),
    (7, "一周内"),
    (3, "三日内"),
)


def _published_within_days(published_at: str, days: int) -> bool:
    if days <= 0:
        return True
    try:
        published = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        if published.tzinfo is None:
            published = published.replace(tzinfo=timezone.utc)
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        return published.astimezone(timezone.utc) >= cutoff
    except (TypeError, ValueError):
        return False


def create_app(settings: Settings | None = None) -> Flask:
    settings = settings or Settings()
    settings.prepare()
    app = Flask(__name__)
    repository = Repository(settings.database_path)

    @app.get("/")
    def index():
        results = repository.latest_results(limit=1000)
        minimum = request.args.get("minimum", default=0, type=int)
        event_type = request.args.get("event_type", default="")
        days = request.args.get("days", default=0, type=int)
        valid_days = {value for value, _ in DATE_RANGES}
        if days not in valid_days:
            days = 0
        filtered = [
            row
            for row in results
            if row["analysis"]["relevance_score"] >= minimum
            and (not event_type or row["analysis"]["event_type"] == event_type)
            and _published_within_days(row["item"]["published_at"], days)
        ]
        event_types = sorted({row["analysis"]["event_type"] for row in results})
        return render_template(
            "index.html",
            results=filtered,
            total=len(results),
            high=sum(row["analysis"]["relevance_score"] >= 60 for row in results),
            event_types=event_types,
            minimum=minimum,
            selected_type=event_type,
            date_ranges=DATE_RANGES,
            selected_days=days,
            model=settings.llm_model if settings.llm_api_key else "规则引擎",
        )

    @app.post("/run")
    def run_pipeline():
        RadarPipeline(settings).run()
        return redirect(url_for("index"))

    @app.get("/api/results")
    def api_results():
        return jsonify(repository.latest_results(limit=100))

    @app.get("/health")
    def health():
        return {"status": "ok", "items": repository.count_items()}

    return app