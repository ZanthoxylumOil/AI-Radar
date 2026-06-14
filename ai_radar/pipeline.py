from __future__ import annotations

import logging

from .analyzer import Analyzer
from .collectors import FeedCollector
from .config import Settings
from .report import build_markdown, save_report
from .storage import Repository

LOGGER = logging.getLogger(__name__)


class RadarPipeline:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()
        self.settings.prepare()
        self.repository = Repository(self.settings.database_path)
        self.collector = FeedCollector(timeout=self.settings.request_timeout)
        self.analyzer = Analyzer(
            api_key=self.settings.llm_api_key,
            base_url=self.settings.llm_base_url,
            model=self.settings.llm_model,
            timeout=self.settings.llm_timeout,
        )

    def run(self) -> dict:
        items = self.collector.collect(
            self.settings.load_sources(),
            max_items=self.settings.max_items_per_source,
            lookback_hours=self.settings.lookback_hours,
        )
        inserted = self.repository.save_items(items)
        pending = self.repository.pending_items(limit=200)
        for item in pending:
            self.repository.save_analysis(self.analyzer.analyze(item))
        results = self.repository.latest_results(limit=200)
        report_path = save_report(build_markdown(results), self.settings.report_dir)
        summary = {
            "collected": len(items),
            "inserted": inserted,
            "analyzed": len(pending),
            "total_results": len(results),
            "report": str(report_path),
            "analysis_mode": self.settings.llm_model
            if self.settings.llm_api_key
            else "rule-engine",
        }
        LOGGER.info("Pipeline completed: %s", summary)
        return summary