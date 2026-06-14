from __future__ import annotations

import argparse
import json
import logging
import threading
import webbrowser

from apscheduler.schedulers.blocking import BlockingScheduler

from .analyzer import Analyzer
from .config import Settings
from .pipeline import RadarPipeline
from .report import build_markdown, save_report
from .sample_data import sample_items
from .storage import Repository


def open_browser(host: str, port: int, delay: float = 1.0) -> threading.Timer:
    browser_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
    url = f"http://{browser_host}:{port}"
    timer = threading.Timer(delay, webbrowser.open, args=(url,))
    timer.daemon = True
    timer.start()
    return timer


def run_demo(settings: Settings) -> dict:
    settings.prepare()
    repository = Repository(settings.database_path)
    items = sample_items()
    inserted = repository.save_items(items)
    analyzer = Analyzer()
    pending = repository.pending_items()
    for item in pending:
        repository.save_analysis(analyzer.analyze(item))
    results = repository.latest_results()
    path = save_report(build_markdown(results), settings.report_dir)
    return {
        "inserted": inserted,
        "analyzed": len(pending),
        "total_results": len(results),
        "report": str(path),
        "analysis_mode": "offline-demo",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="AI前沿证券量化情报智能体")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("run", help="立即采集、分析并生成报告")
    subparsers.add_parser("demo", help="使用离线样例生成演示报告")
    schedule = subparsers.add_parser("schedule", help="按固定间隔持续运行")
    schedule.add_argument("--hours", type=int, default=6, help="运行间隔（小时）")
    serve = subparsers.add_parser("serve", help="启动Web控制台")
    serve.add_argument("--host", default="0.0.0.0")
    serve.add_argument("--port", type=int, default=8000)
    serve.add_argument(
        "--no-browser",
        action="store_true",
        help="不自动打开默认浏览器（适用于服务器或容器）",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    settings = Settings()
    if args.command == "run":
        print(json.dumps(RadarPipeline(settings).run(), ensure_ascii=False, indent=2))
    elif args.command == "demo":
        print(json.dumps(run_demo(settings), ensure_ascii=False, indent=2))
    elif args.command == "schedule":
        pipeline = RadarPipeline(settings)
        scheduler = BlockingScheduler()
        scheduler.add_job(
            pipeline.run,
            "interval",
            hours=max(args.hours, 1),
            max_instances=1,
            coalesce=True,
        )
        pipeline.run()
        scheduler.start()
    elif args.command == "serve":
        from .web import create_app

        if not args.no_browser:
            open_browser(args.host, args.port)
        create_app(settings).run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()