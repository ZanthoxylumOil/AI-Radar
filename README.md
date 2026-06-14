# AI-Radar

## 这个智能体能做什么
- 自动采集国内外 AI 相关技术、产品、政策和金融相关新闻
- 去重、完成相关度排序
- 给出对投资影响分析
- 生成可追溯的报告

## 如何让它跑起来

在项目根目录运行指令启动程序，随后自动使用默认浏览器打开 `http://127.0.0.1:8000`。

```bash
# 离线时可使用此命令加载演示数据，联网时可忽略
python -m ai_radar.cli demo
```
```bash
python -m ai_radar.cli serve
```

抓取的数据存放在`data`，生成的报告存放在`reports`。

#### 环境配置
- Python：3.10+
- Web：Flask
- 存储：SQLite
- 采集：RSS/Atom、arXiv API
- 模型：任意 OpenAI Chat Completions 兼容接口
- 无密钥模式：内置规则引擎，可离线完成演示

#### 模型配置

`.env` 支持 OpenAI、DeepSeek、通义千问等提供 OpenAI 兼容接口的服务：

```dotenv
LLM_API_KEY=your-key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4.1-mini
```

#### 数据源配置

编辑 `config/sources.json` 即可增删 RSS/Atom 源。每个数据源包含：

```json
{"name": "来源名", "url": "订阅地址", "region": "china", "category": "news"}
```


## 系统核心结构
```bash
ai_radar/
├── models.py             # 数据模型
├── config.py             # 环境变量和数据源配置
├── collectors.py         # RSS/Atom 情报采集
├── analyzer.py           # LLM/规则分析
├── storage.py            # SQLite 持久化
├── report.py             # Markdown 报告生成
├── pipeline.py           # 完整业务流程编排
├── sample_data.py        # 离线演示数据
├── cli.py                # 命令行入口及定时任务
├── web.py                # Flask Web/API
├── templates/index.html  # Web 页面模板
└── static/style.css      # 页面样式
```