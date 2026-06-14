from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .models import NewsItem


def sample_items() -> list[NewsItem]:
    now = datetime.now(timezone.utc)
    return [
        NewsItem(
            id="demo-model-agent-001",
            source="离线演示数据",
            title="新一代多模态智能体模型发布，强化工具调用与长上下文能力",
            url="https://example.com/demo/model-agent",
            summary="该模型面向企业工作流，支持文本、图像和结构化工具调用。此条为离线演示，不代表真实新闻。",
            published_at=(now - timedelta(hours=2)).isoformat(timespec="seconds"),
            region="global",
            category="product",
        ),
        NewsItem(
            id="demo-chip-002",
            source="离线演示数据",
            title="AI推理芯片新品公布，重点降低数据中心单位推理成本",
            url="https://example.com/demo/inference-chip",
            summary="厂商公布新架构和能效数据，量产、供货与实际性能仍待验证。此条为离线演示。",
            published_at=(now - timedelta(hours=5)).isoformat(timespec="seconds"),
            region="china",
            category="product",
        ),
        NewsItem(
            id="demo-regulation-003",
            source="离线演示数据",
            title="生成式人工智能监管指引更新，强调数据治理和模型风险评估",
            url="https://example.com/demo/ai-regulation",
            summary="指引要求加强训练数据、输出内容和第三方模型管理。此条为离线演示。",
            published_at=(now - timedelta(hours=8)).isoformat(timespec="seconds"),
            region="china",
            category="regulation",
        ),
    ]