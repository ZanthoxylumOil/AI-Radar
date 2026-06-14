from __future__ import annotations

from collections import Counter
from datetime import datetime
from pathlib import Path


def build_markdown(results: list[dict], generated_at: datetime | None = None) -> str:
    generated_at = generated_at or datetime.now().astimezone()
    high = [row for row in results if row["analysis"]["relevance_score"] >= 60]
    event_counts = Counter(row["analysis"]["event_type"] for row in results)
    lines = [
        "# AI前沿情报与证券量化影响报告",
        "",
        f"- 生成时间：{generated_at:%Y-%m-%d %H:%M %Z}",
        f"- 分析事件：{len(results)} 条",
        f"- 高相关事件：{len(high)} 条",
        f"- 免责声明：本报告由自动化系统生成，仅供研究，不构成投资建议。",
        "",
        "## 执行摘要",
        "",
    ]
    if results:
        trend = "、".join(f"{name} {count}条" for name, count in event_counts.most_common(4))
        lines.append(f"本期事件主要分布为：{trend}。应优先复核高相关事件的原始来源和上市公司公告。")
    else:
        lines.append("本期暂无已分析事件。请检查网络、数据源配置或扩大回溯时间。")

    lines.extend(["", "## 重点事件", ""])
    for index, row in enumerate(results[:15], 1):
        item, analysis = row["item"], row["analysis"]
        lines.extend(
            [
                f"### {index}. {item['title']}",
                "",
                f"- 来源：[{item['source']}]({item['url']})",
                f"- 时间：{item['published_at']} | 地区：{item['region']}",
                f"- 相关度：{analysis['relevance_score']}/100 | 事件类型：{analysis['event_type']} | 置信度：{analysis['confidence']}",
                f"- 证券行业影响：{analysis['securities_impact']}",
                f"- 量化投资影响：{analysis['quant_impact']}",
                f"- 机会：{'；'.join(analysis['opportunities'])}",
                f"- 风险：{'；'.join(analysis['risks'])}",
                f"- 建议：{'；'.join(analysis['recommendations'])}",
                "",
            ]
        )
    lines.extend(
        [
            "## 使用边界",
            "",
            "1. 新闻不等同于可交易事实，重大信息须回溯监管披露、公司公告或论文原文。",
            "2. 评分用于情报排序，不是收益预测；禁止未经回测直接接入实盘。",
            "3. 大模型分析可能出现遗漏或幻觉，所有结论需保留来源与人工复核记录。",
            "",
        ]
    )
    return "\n".join(lines)


def save_report(content: str, report_dir: Path) -> Path:
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / f"ai_radar_{datetime.now():%Y%m%d_%H%M%S}.md"
    path.write_text(content, encoding="utf-8")
    (report_dir / "latest.md").write_text(content, encoding="utf-8")
    return path