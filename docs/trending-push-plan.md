# GitHub Trending 自动推送方案

> 文档版本：v0.1（分析草稿）
> 日期：2026-07-09
> 状态：待讨论

---

## 一、需求概述

定时抓取 GitHub Trending 仓库列表，经 LLM 摘要处理后，推送到指定渠道供用户消费。

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  采集层   │ →  │  处理层   │ →  │  存储层   │ →  │  推送层   │
│ Trending  │    │ LLM 摘要  │    │  DB/缓存  │    │ 多通道分发 │
│ 页面抓取  │    │ 分类/筛选  │    │          │    │          │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
                                                     ↑
                                              ┌──────────┐
                                              │  触发层   │
                                              │ Cron/GH  │
                                              │ Action/  │
                                              │ Hermes   │
                                              └──────────┘
```

---

## 二、数据源分析

### 2.1 GitHub Trending 页面

| 项目 | 说明 |
|------|------|
| URL | `https://github.com/trending?since=daily&language=python` |
| 页面类型 | 静态 HTML（无 API） |
| 更新频率 | 每 ~2–4 小时更新一次 |
| 返回字段 | repo 全名、描述、语言、今日 star 数、总 star 数、fork 数 |
| 技术参考 | `article.Box-row` + CSS class 选择器定位各字段 |

### 2.2 抓取方案对比

| 方案 | 维护成本 | 可靠性 | 速率限制 | 推荐 |
|------|---------|--------|---------|------|
| **requests + BeautifulSoup** 直抓 | 低 | 依赖页面结构，GitHub 改版会断 | 设 User-Agent 可过，频繁会 429 | ✅ 初版 |
| **Playwright/Selenium** 无头浏览器 | 高 | 不受结构变化影响 | 可模拟真人行为 | 页面大改时用 |
| **第三方 API（huchenme 等）** | 低 | 第三方服务可能挂 | 取决于提供商 | 做备选 |
| **GitHub Search API** | 低 | 数据不同（不是 Trending 逻辑） | 60/hr 未认证，5000/hr 认证 | ❌ |

**初版建议**：直接用 `requests` + `BeautifulSoup`，加上简单的缓存逻辑（同一 since 周期内不重复抓）。

### 2.3 Python 数据模型

```python
@dataclass
class TrendingRepo:
    owner: str                    # littleyellowbicycle
    name: str                     # cos2edu
    url: str                      # https://github.com/littleyellowbicycle/cos2edu
    description: str              # 叙事驱动的苏格拉底式 AI 教学系统
    language: str                 # Python
    stars_total: int              # 1234
    stars_today: int              # 56
    forks: int                    # 89
    builders: list[str]           # ["contributor1", ...]
    since: str                    # daily / weekly / monthly
    fetched_at: datetime

@dataclass
class TrendingSnapshot:
    id: str                       # uuid
    since: str
    language: str | None          # None = all languages
    repos: list[TrendingRepo]
    summary: str | None           # LLM 生成的摘要
    fetched_at: datetime
    pushed: bool                  # 是否已推送
```

---

## 三、触发层（Trigger）

### 3.1 方案对比

| 方案 | 适用场景 | 优点 | 缺点 |
|------|---------|------|------|
| **GitHub Actions (cron)** | 项目已有 GitHub 仓库 | 零成本、无需服务器、日志内置 | 最小间隔 1h，不适合高频率 |
| **APScheduler（后端进程内）** | 后端已 7×24 运行（桌面版也适用） | 精确到秒，进程内无需额外部署 | 后端重启定时丢失，单机 |
| **Celery + Redis** | 后端已有 Redis 部署 | 分布式、可靠、任务队列解耦 | 需 Redis，架构变复杂 |
| **Hermes** | 已有 Hermes 消息队列 | 原生可靠投递 | 需额外搭建 Hermes 集群 |

**推荐路径**：

```
Step 1（快速上线）：GitHub Actions cron 触发 → 服务器执行抓取 → 推送
Step 2（稳定运行）：APScheduler 嵌入后端，桌面版开机自启即带定时任务
Step 3（高可靠）：如需 Celery / Hermes，在规模扩大后迁入
```

### 3.2 GitHub Actions 方案

```yaml
# .github/workflows/fetch-trending.yml
name: Fetch GitHub Trending

on:
  schedule:
    - cron: '0 8,20 * * *'   # 每天 UTC 8:00 / 20:00（北京时间 16:00 / 4:00）
  workflow_dispatch:          # 支持手动触发

jobs:
  fetch:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install requests beautifulsoup4 httpx
      - run: python scripts/fetch_trending.py
        env:
          PUSH_CHANNEL: ${{ secrets.PUSH_CHANNEL }}     # wechat / feishu / email
          WEBHOOK_URL: ${{ secrets.WEBHOOK_URL }}
          LLM_API_KEY: ${{ secrets.LLM_API_KEY }}
      - uses: actions/upload-artifact@v4
        with:
          name: trending-snapshot
          path: data/trending-latest.json
```

### 3.3 APScheduler 方案（嵌入后端）

无需额外基础设施，直接集成到现有 FastAPI 后端：

```python
# backend/app/tasks/trending_scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger


scheduler = AsyncIOScheduler()


def init_trending_scheduler(app: FastAPI):
    """在 lifespan 中调用"""
    scheduler.add_job(
        fetch_and_push_trending,
        CronTrigger(hour="8,20", timezone="Asia/Shanghai"),
        id="trending_daily",
        replace_existing=True,
    )
    scheduler.start()


async def fetch_and_push_trending():
    """采集 → LLM 摘要 → 推送"""
    repos = await scrape_trending()
    summary = await llm_summarize(repos[:10])
    await push_to_channels(summary, repos)
```

**依赖**：
```bash
pip install apscheduler
```

### 3.4 Hermes / 龙虾 方案

**Hermes（消息队列调度）**：
- 适合已有事件驱动架构
- 用 Hermes 定时生产消息 → 消费者执行抓取→推送链路
- 与 APScheduler 的差别在于：Hermes 负责"定时触发"而非"定时执行"，下游可多消费者并行

**龙虾（轻量调度器替代方案）**：
- 这是一个可选的 cron 替代品，用于在桌面端或轻量服务器上运行
- 比 APScheduler 更轻量，无需 asyncio 依赖
- 适用于 PyInstaller 打包后的桌面版

---

## 四、采集层

### 4.1 核心抓取逻辑

```python
# scripts/fetch_trending.py
import requests
from bs4 import BeautifulSoup

TRENDING_URL = "https://github.com/trending"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
}


def fetch_trending(language: str = "", since: str = "daily") -> list[dict]:
    params = {}
    if language:
        params["language"] = language
    if since:
        params["since"] = since

    resp = requests.get(TRENDING_URL, params=params, headers=HEADERS, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    repos = []

    for article in soup.select("article.Box-row"):
        title_el = article.select_one("h2.h3 a.Link")
        if not title_el:
            continue
        href = title_el.get("href", "").strip("/")
        owner, name = href.split("/") if "/" in href else ("", href)

        desc_el = article.select_one("p.color-fg-muted")
        lang_el = article.select_one('[itemprop="programmingLanguage"]')
        stars_el = article.select_one("a.Link--muted")
        today_el = article.select_one("span.float-sm-right")

        builders = [img.get("alt", "") for img in article.select("img.avatar")]

        repos.append({
            "owner": owner,
            "name": name,
            "url": f"https://github.com/{owner}/{name}",
            "description": desc_el.text.strip() if desc_el else "",
            "language": lang_el.text.strip().rstrip() if lang_el else "",
            "stars_today": _parse_stars(today_el),
            "builders": builders,
            "since": since,
        })

    return repos


def _parse_stars(el) -> int:
    if not el:
        return 0
    text = el.text.strip()
    # "524 stars today" → 524
    import re
    match = re.search(r"(\d[\d,]*)", text.replace(",", ""))
    return int(match.group(1)) if match else 0
```

### 4.2 缓存策略

```
┌─────────────────────────────────────────┐
│  Key: trending:{language}:{since}        │
│  TTL: 4 hours（Trending 页面本身缓存周期）│
│  Value: TrendingSnapshot (JSON)          │
│                                          │
│  Redis / SQLite / JSON file 均可         │
└─────────────────────────────────────────┘
```

- 如果缓存命中且未过期，跳过抓取
- 如果缓存过期或不存在，抓取后写入缓存
- 推送成功后标记 `pushed: true`，避免重复推送

---

## 五、处理层（LLM 摘要）

利用项目中已有的 LLM 能力：

```python
async def llm_summarize(repos: list[dict], top_n: int = 10) -> str:
    """
    用 LLM 生成今日 Trending 摘要。
    复用项目中已有的 LLMProvider / OpenAI / Anthropic 等。
    """
    repo_text = "\n".join(
        f"{i+1}. [{r['name']}]({r['url']}) — {r['description'] or '无描述'} "
        f"(⭐{r['stars_today']} today, {r['language']})"
        for i, r in enumerate(repos[:top_n])
    )

    prompt = f"""你是一位技术趋势分析师。以下是 GitHub 今日 Trending 仓库列表。
请用中文写一段 200 字以内的摘要，突出最值得关注的项目和整体趋势趋势。

{repo_text}"""

    # 复用项目已有的 LLM 调用链路
    from app.llm.provider import LLMProvider
    provider = LLMProvider(model="gpt-4o-mini")  # mini 即可，成本低
    summary = await provider.chat([
        {"role": "system", "content": "你是一个简洁的技术趋势分析师。"},
        {"role": "user", "content": prompt},
    ])
    return summary
```

---

## 六、推送层

### 6.1 推送渠道对比

| 渠道 | 接入成本 | 到达率 | 适合场景 |
|------|---------|--------|---------|
| **企业微信机器人** | 低 — webhook URL 即可 | 高 | 团队内部 |
| **Server 酱** | 低 — API Key 绑定微信 | 中（需关注公众号） | 个人开发者 |
| **飞书机器人** | 低 — webhook URL 即可 | 高 | 团队内部 |
| **钉钉机器人** | 低 — webhook URL 即可 | 高 | 团队内部 |
| **邮件** | 中 — 需 SMTP 配置 | 中（进垃圾箱风险） | 个人 |
| **应用内推送** | 高 — 需 WebSocket 接入 | 仅应用打开时 | 桌面版用户 |

### 6.2 推送格式

```python
import httpx


async def push_via_webhook(webhook_url: str, title: str, content: str, channel: str):
    """支持企业微信 / 飞书 / 钉钉 三种格式"""

    if channel == "wecom":  # 企业微信
        payload = {
            "msgtype": "markdown",
            "markdown": {"content": f"# {title}\n{content}"},
        }
    elif channel == "feishu":  # 飞书
        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {"title": {"tag": "plain_text", "content": title}},
                "elements": [{"tag": "markdown", "content": content}],
            },
        }
    elif channel == "dingtalk":  # 钉钉
        payload = {
            "msgtype": "markdown",
            "markdown": {"title": title, "text": f"# {title}\n{content}"},
        }
    elif channel == "sct":  # Server 酱
        payload = {"title": title, "desp": content.replace("\n", "\n\n")}
        webhook_url = f"https://sctapi.ftqq.com/{webhook_url}.send"

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(webhook_url, json=payload)
        resp.raise_for_status()
```

### 6.3 应用内推送（WebSocket）

对于桌面版用户，可以复用项目中现有的 WebSocket 连接：

```json
// 服务端 → 客户端
{
  "type": "trending.push",
  "payload": {
    "snapshot_id": "xxx",
    "since": "daily",
    "summary": "今日 AI 领域…",
    "repos": [
      {
        "name": "owner/repo",
        "url": "https://github.com/owner/repo",
        "description": "…",
        "stars_today": 524,
        "language": "Python"
      }
    ]
  }
}
```

对应前端新增 `TrendingCard.vue` 来展示，注册为 Generative UI 组件。

---

## 七、多方案对比总结

```
方案              触发方式      运行位置        适合阶段    运维成本
─────────────────────────────────────────────────────────────
GH Actions        cron          GitHub 服务器    ⭐ 初版   最低
APScheduler       cron          后端进程内       进阶      低
Celery + Redis    crontab/beat  独立 Worker     高负载     中
Hermes            定时消息      消息队列          大规模     高
龙虾              定时任务      桌面版/轻量服务   桌面版    低
```

---

## 八、桌面版集成

结合之前的桌面打包方案，桌面版用户的后端是常驻进程的，可以直接用 APScheduler：

```
                                  ┌──────────────────────────┐
                                  │  桌面版后端 (常驻进程)     │
                                  │                          │
┌──────────────────┐              │  APScheduler             │
│  8:00 AM         │──────────→   │    │                    │
│  CronTrigger     │              │    ├─ scrape_trending()  │
│  (时区感知)       │              │    ├─ llm_summarize()   │
└──────────────────┘              │    ├─ push_to_app() ← WebSocket
                                  │    └─ push_to_wechat()  │
                                  └──────────────────────────┘
```

用户启动桌面版后，后端自动注册定时任务。无需服务器，用户关掉应用则暂停，下次启动自动恢复。

---

## 九、推荐实施路径

### Step 1：MVP（1–2 天）

- 用 `requests` + `BeautifulSoup` 写抓取脚本
- 用 GitHub Actions cron 触发
- 推送目标：企业微信 / Server 酱（选其一）
- 输出 JSON 文件到仓库 artifact

```
┌──────────────┐    ┌───────────────┐    ┌────────────────┐
│ GH Actions   │ →  │ fetch_and_    │ →  │ webhook push   │
│ cron 8:00    │    │ summarize.py  │    │ (企微/SCT)     │
│ 20:00 UTC    │    │               │    │                │
└──────────────┘    └───────────────┘    └────────────────┘
```

### Step 2：应用内集成（2–3 天）

- APScheduler 嵌入后端
- 新增 WebSocket `trending.push` 消息类型
- 前端新增 `TrendingCard.vue` 组件
- 桌面版开机即带定时推送

### Step 3：优化（按需）

- 多语言 filter（Python / Rust / Go 分类推送）
- 个性化订阅（用户只关注某些语言）
- 用 LLM 生成更详细的「为什么这个项目值得关注」推荐语

---

## 十、风险与应对

| 风险 | 影响 | 应对 |
|------|------|------|
| GitHub 页面结构改版 | 抓取失败 | 加 CSS selector 测试；备选 Playwright |
| IP 被限 (429) | 抓取中断 | GitHub Action 自带 GitHub IP，不易被限；备用时加 3s delay |
| LLM API Key 泄露 | 被盗用产生费用 | 存在 GitHub Secrets 中；限制 model 为 gpt-4o-mini（成本低） |
| 桌面版后端不常开 | 定时任务不执行 | 用 GitHub Actions 兜底，桌面版仅作为补充 |
| Trending 重复推送 | 用户烦 | 缓存去重 + `pushed` 标记；同一 since 周期只推一次 |

---

## 附录：引用文件

| 文件/资源 | 用途 |
|----------|------|
| `.github/workflows/fetch-trending.yml` | GitHub Actions 定时工作流（待创建） |
| `scripts/fetch_trending.py` | 抓取 + 摘要 + 推送 脚本（待创建） |
| `backend/app/tasks/trending_scheduler.py` | APScheduler 嵌入方案（待创建） |
| `frontend/src/components/generative/TrendingCard.vue` | 应用内展示组件（待创建） |
| `backend/app/schemas/ws_protocol.py` | 需新增 `trending.push` 消息类型 |