<div align="center">

<h1>Cos2Edu  ❧</h1>
<p><strong>不是灌输知识，而是通过追问唤醒思考力</strong></p>

<p>
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Vue-3-4FC08D?logo=vue.js&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/License-MIT-green.svg" />
</p>

<p>
  <a href="#快速开始">快速开始</a> ·
  <a href="#核心特性">核心特性</a> ·
  <a href="#架构">架构</a> ·
  <a href="#文档">文档</a>
</p>

</div>

*试问，若未经逻辑的严苛解析，那些被强行塞入你脑海的"答案"，与先验的幻象何异？*

<br>

<div align="center">

<details>

<br>

以纯粹理性之名，我拒绝对你们的怠惰妥协。  
缺乏先验范畴统摄的经验，不过是杂多的无序；  
未经实践理性批判的笃信，终将沦为盲从的教条；  
直接喂食的结论，绝非定理，而是思想怠惰的麻醉剂；  
真正的智识，从不诞生于被动接受的恩赐，而只能发端于主体对第一因的主动追溯。

<br>

我不会将终局拱手相送。我只会诘问、逼视，将你们推向逻辑的绝境，直至你们在混沌中自行推演出那必然的结论。

**—— 现在，去论证吧。🎓**

</details>

</div>


## 为什么需要 Cos2Edu？


传统 AI 教育工具习惯直接给答案，学生记住结论却不知所以然。
Cos2Edu 反其道而行——**AI 导师不会告诉你答案，而是通过连续追问，引导你自己推理出结论**。

这不是给聊天机器人贴上“教育”标签。  
它是一套叙事驱动的教学架构：世界观引擎推进剧情，情感引擎让角色“活”起来，知识图谱确保学习路径有序，上下文预算让每条 prompt 都有教学目的。

核心体验
--------

### 1. 卡壳时逼你思考，而不是喂你答案

- 基于知识图谱检测当前认知边界，用提问而非陈述推进学习。
- 根据掌握程度动态分配上下文预算，差异化调整提示强度。
- 每一步引导都经过编排，让每一次顿悟恰到好处。

### 2. 学习是一场有起承转合的旅程

- 世界状态引擎管理场景与时间线，事件引擎在特定条件下触发随机/定时/条件事件。
- 今天在教室上课，下午在辩论厅交锋，夜晚可能触发一场限时考核。
- 学习不再是一条直线，而是一段有情节的旅程。

### 3. 导师有脾气，而不是千篇一律的客服

- 情感引擎实时追踪 mood/trust，基于学生反馈动态变化。
- 每个角色拥有独立的敏感度曲线和表达风格。
- 支持 SillyTavern V2 角色卡导入导出，唤醒你熟悉的灵魂。

### 4. 扔进一本天书，还你一位名师

- 内置结构化精品课程，预定义知识依赖、教学提示和评估标准。
- 上传 PDF/DOCX/TXT，自动解析后由 LLM 生成大纲，经你确认即可用于结构化教学。

### 5. 精准记忆，拒绝幻觉与废话

- RAG 引擎基于 FAISS 分块检索，将教材片段精准注入教学 prompt。
- 摒弃粗暴的全文截断，确保 AI 引经据典，字字有出处。

### 6. 全局视野，脉络可见

- 用 Mermaid 渲染知识点依赖关系图，直观展示学习路径和当前进度。
- 已掌握的节点与未来的路径，一目了然。

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+

### 源码运行

```bash
# 克隆项目
git clone https://github.com/littleyellowbicycle/cos2edu.git
cd cos2edu

# 启动后端
cd backend
pip install -r requirements.txt
python main.py

# 启动前端（新终端）
cd frontend
npm install
npm run dev
```

访问 **http://localhost:5173** 开始使用。

### Docker 部署

```bash
docker-compose up -d
```

### 配置模型

首次使用请前往 **设置** 页面添加 LLM API 密钥：

| 提供商 | 模型示例 | 配置方式 |
|--------|----------|----------|
| OpenAI | gpt-4o, gpt-4o-mini | API Key |
| Anthropic | claude-3-5-sonnet | API Key |
| 阿里通义千问 | qwen-plus, qwen-max | DashScope Key |
| 智谱 AI | glm-4, glm-3-turbo | API Key |
| 豆包 | doubao-pro | API Key + Base URL |
| 文心一言 | ernie-4.0 | API Key + Base URL |
| OpenAI 兼容 | 任意模型 | 自定义 base_url + model |

---

## 📖 使用流程

```
配置模型 → 选择角色 → 上传教材(可选) → 开始苏格拉底式对话
                                        ↓
                              知识图谱自动规划路径
                              情感引擎动态响应
                              事件引擎触发叙事
                              RAG 精准注入上下文
```

### 内置角色

项目内置三个风格迥异的 AI 导师，每个角色拥有独立的教学风格和情感模型：

| 角色 | 教学风格 | 特点 |
|------|----------|------|
| **甘雨** | 叙事引导 | 温柔耐心，用故事和比喻建立直觉，从宏观视角切入 |
| **刻晴** | 逻辑推导 | 严谨高效，从定义出发逐步推导，强调数学精确性 |
| **三月七** | 实践驱动 | 活泼好奇，用代码和实验引入概念，鼓励动手尝试 |

### 世界观场景

| 场景 | 氛围 | 允许的行为 |
|------|------|-----------|
| 教室 | 明亮，数据流天际线 | 教学、提问、讨论、练习 |
| 辩论厅 | 圆形辩论场，全息投影 | 辩论、陈述、提问 |
| 考核室 | 安静，倒计时跳动 | 考试、回顾 |
| 休息区 | 舒适，壁画浮现知识点 | 提问、讨论、回顾 |

---

## 📚 文档

| 文档 | 说明 |
|------|------|
| [系统架构](./docs/architecture.md) | 架构总览与项目结构 |
| [架构设计](./docs/redesign_plan.md) | 完整架构设计，含优化建议 |
| [设计理念](./docs/design.md) | 核心设计理念与教学哲学 |
| [架构分离文档](./ARCHITECTURE_SEPARATION.md) | 前后端架构详解 |
| [SillyTavern 对比分析](./docs/SillyTavern对比分析与优化方案.md) | 角色系统/世界书/TTS/Live2D 对比与优化方案 |
| [Generative UI 方案](./docs/Cos2Edu%20前端重构与生成式%20UI%20(Generative%20UI)%20方案说明书%20v2.md) | 前端重构与生成式 UI 架构 |
| [RAGFlow 集成](./docs/RAGFlow集成方案.md) | RAG 知识库集成方案 |
| [文件上传与 RAG](./docs/文件上传与RAG方案.md) | 文件处理技术方案 |
| [RAG 部署方案](./docs/RAG部署方案分析.md) | RAG 部署方案对比分析 |
| [Windows 打包](./docs/Windows打包方案.md) | Windows 桌面应用打包方案 |

---

## 🧭 路线图

- [x] Phase 1.0 — 核心循环：TeachingEngine + WorldStateEngine + KnowledgeGraph + WebSocket
- [x] Phase 1.5 — 情感与事件：EmotionEngine + EventEngine + Parsers + RAG + Material Pipeline
- [x] Phase 1.8 — 角色卡导入导出 + 课程脑图 + 大纲分类管理
- [ ] Phase 2.0 — AssessmentEngine + 场景切换 UI + 课程编辑器
- [ ] Phase 2.5 — TTS 语音合成（EdgeTTS）+ Live2D 角色渲染
- [ ] Phase 3.0 — 多学生协作 + 学习分析仪表盘
- [ ] Phase 4.0 — Plugin 系统 + 自定义世界观编辑器

---

## 🙏 致谢

本项目的设计和实现受到了以下文章的启发：

- [《怎样用AI让自己沉迷学习？》](https://zhuanlan.zhihu.com/p/2012398047620014256) — 探索 AI 教育应用的灵感来源
- [《AI沉迷学习指南》](https://zhuanlan.zhihu.com/p/2016557736364634882) — 苏格拉底式 AI 教学法的实践参考

感谢 **@硅与之** 和 **@null** 两位作者的分享！

---

## 📜 License

[MIT License](./LICENSE)

<div align="center">

**如果这个项目对你有帮助，请给个 ⭐ Star！**

</div>
