# 苏格拉底AI教学系统

基于苏格拉底教学法的 AI 教学系统，让 AI 导师通过提问引导你自主思考。

## 功能特点

- 🧠 **苏格拉底教学法** - 不直接给出答案，通过问题引导自主思考
- 🎭 **个性化角色** - 选择不同性格的 AI 导师
- 📚 **自定义教材** - 上传教材内容，AI 基于教材进行教学
- 🔧 **多模型支持** - OpenAI、Anthropic、阿里通义千问、智谱 AI 等
- 💻 **本地部署** - 完全本地运行，数据安全私密
- 📦 **绿色打包** - 一键打包为 Windows 可执行程序，解压即用

## 快速开始

### 方式一：源码运行

```bash
# 后端
cd backend
pip install -r requirements.txt
python main.py

# 前端
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173

### 方式二：Docker 部署

```bash
docker-compose up -d
```

### 方式三：Windows 绿色版（打包后）

直接运行 `cos2edu.exe` 或双击 `启动.bat`

**打包方法**：`cd packaging && .\build.bat`

## 使用流程

1. **配置模型** - 在设置页面添加你的 LLM API 密钥
2. **添加教材** - 在教材管理页面添加学习内容
3. **选择角色** - 选择一个喜欢的 AI 导师角色
4. **开始学习** - 创建新对话，与 AI 导师进行苏格拉底式对话

## 项目结构

```
cos2edu/
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── api/            # API 路由
│   │   ├── core/           # 核心配置
│   │   ├── models/         # 数据模型
│   │   ├── repositories/   # 数据访问层
│   │   └── services/       # 业务逻辑
│   └── main.py             # 入口文件
├── frontend/                # Vue 3 前端
│   └── src/
│       ├── views/          # 页面组件
│       ├── api/            # API 调用
│       └── stores/         # 状态管理
├── docs/                    # 技术方案文档
├── packaging/                # 打包配置和脚本
└── README.md               # 本文件
```

## 文档目录

| 文档 | 说明 |
|------|------|
| [Windows打包方案.md](./docs/Windows打包方案.md) | PyInstaller 打包详细方案 |
| [RAGFlow集成方案.md](./docs/RAGFlow集成方案.md) | RAG 知识库集成方案 |
| [文件上传与RAG方案.md](./docs/文件上传与RAG方案.md) | 文件处理与 RAG 技术方案 |
| [ARCHITECTURE_SEPARATION.md](./ARCHITECTURE_SEPARATION.md) | 架构设计文档 |

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3, Pinia, Element Plus |
| 后端 | FastAPI, SQLAlchemy 2.0, Pydantic 2.0 |
| 数据库 | SQLite / PostgreSQL |
| LLM | OpenAI, Anthropic, 通义千问, 智谱 AI 等 |

## 支持的模型提供商

| 提供商 | 环境变量 | 常见模型 |
|--------|----------|----------|
| OpenAI | OPENAI_API_KEY | gpt-4o, gpt-3.5-turbo |
| Anthropic | ANTHROPIC_API_KEY | claude-3-5-sonnet |
| 阿里通义千问 | DASHSCOPE_API_KEY | qwen-plus, qwen-max |
| 智谱 AI | ZHIPU_API_KEY | glm-4, glm-3-turbo |

## 苏格拉底教学法

苏格拉底教学法的核心是**提问而非灌输**：

1. **不直接给出答案** - 让学生自己推理
2. **循序渐进的问题** - 从已知到未知
3. **关注推理过程** - 答案不重要，思考过程才重要
4. **鼓励质疑精神** - 培养批判性思维

---

## 致谢

本项目的设计和实现受到了以下文章的启发：

- [《怎样用AI让自己沉迷学习？》](https://zhuanlan.zhihu.com/p/2012398047620014256) - 探索 AI 教育应用的灵感来源
- [《AI沉迷学习指南》](https://zhuanlan.zhihu.com/p/2016557736364634882) - 苏格拉底式 AI 教学法的实践参考

感谢 **@硅与之** 和 **@null** 两位作者的分享！

## 参考

本项目参考了知乎文章中的教育理念，将苏格拉底教学法与 AI 技术结合，打造沉浸式学习体验。

## License

MIT License