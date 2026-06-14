from __future__ import annotations

import json
import re
from typing import Any

import requests

from .models import Analysis, NewsItem

AI_TERMS = {
    "artificial intelligence": 15, "人工智能": 15,
    "model": 12, "模型": 12, "agent": 12, "智能体": 12, "gpu": 10,
    "芯片": 10, "inference": 9, "推理": 9, "training": 8, "训练": 8,
    "open source": 7, "开源": 7, "regulation": 7, "监管": 7,
}
FINANCE_TERMS = {
    "trading": 15, "quant": 15, "证券": 15, "量化": 15, "investment": 10,
    "投资": 10, "market": 8, "市场": 8, "risk": 6, "风险": 6,
}

SYSTEM_PROMPT = """你是证券行业与量化投资方向的AI情报分析师。
仅依据输入新闻分析，不虚构事实。输出严格JSON对象，字段为：
relevance_score(0-100整数), sentiment(利好/中性/利空), event_type,
securities_impact, quant_impact, opportunities(字符串数组), risks(字符串数组),
recommendations(字符串数组), affected_assets(字符串数组),
time_horizon(短期/中期/长期), confidence(0-1数字)。
建议必须可执行，并明确事实与推测的边界。"""


def _extract_json(text: str) -> dict[str, Any]:
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("Model response contains no JSON object")
    return json.loads(text[start : end + 1])


class Analyzer:
    def __init__(
        self,
        api_key: str = "",
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4.1-mini",
        timeout: int = 60,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def analyze(self, item: NewsItem) -> Analysis:
        if not self.api_key:
            return self._rule_analysis(item)
        try:
            return self._llm_analysis(item)
        except (requests.RequestException, ValueError, KeyError, TypeError):
            result = self._rule_analysis(item)
            result.model = f"rule-engine (fallback from {self.model})"
            return result

    def _llm_analysis(self, item: NewsItem) -> Analysis:
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "temperature": 0.2,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": json.dumps(item.to_dict(), ensure_ascii=False),
                    },
                ],
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = _extract_json(response.json()["choices"][0]["message"]["content"])
        return Analysis(item_id=item.id, model=self.model, **payload)

    def _rule_analysis(self, item: NewsItem) -> Analysis:
        text = f"{item.title} {item.summary}".lower()
        score = 20
        score += sum(weight for term, weight in AI_TERMS.items() if term in text)
        score += sum(weight for term, weight in FINANCE_TERMS.items() if term in text)
        if item.category in {"policy", "regulation"}:
            score += 15
        score = min(score, 100)

        chip = any(term in text for term in ("gpu", "芯片", "semiconductor"))
        regulation = item.category in {"policy", "regulation"} or any(
            term in text
            for term in ("regulation", "监管", "合规", "政策", "办法", "条例", "law")
        )
        product = any(term in text for term in ("launch", "发布", "product", "产品"))
        event_type = "算力与芯片" if chip else "监管政策" if regulation else "产品发布" if product else "技术进展"

        opportunities = ["跟踪事件相关产业链和上市公司的基本面变化"]
        risks = ["新闻信息可能不完整，需与公告和权威来源交叉验证"]
        recommendations = ["纳入研究观察池，未经进一步验证不直接触发交易"]
        assets = ["AI软件与云计算"]
        if chip:
            opportunities.append("关注算力基础设施需求及国产替代")
            risks.append("供应链、出口管制与资本开支周期可能放大波动")
            assets = ["半导体", "数据中心", "云计算"]
        if regulation:
            opportunities.append("合规工具、模型评测与风控服务需求可能上升")
            risks.append("数据、版权、模型备案和跨境合规成本上升")
            recommendations.append("下调缺乏数据治理能力主体的事件暴露")

        return Analysis(
            item_id=item.id,
            relevance_score=score,
            sentiment="中性",
            event_type=event_type,
            securities_impact="可能影响AI产业链估值、券商研究与投顾服务效率，需结合公司披露验证。",
            quant_impact="可作为事件因子和另类数据输入；应控制时效偏差、来源偏差与模型幻觉。",
            opportunities=opportunities,
            risks=risks,
            recommendations=recommendations,
            affected_assets=assets,
            time_horizon="中期",
            confidence=0.55,
        )