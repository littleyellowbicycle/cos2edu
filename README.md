# 苏格拉底AI教学系统

基于苏格拉底教学法的AI教学系统，让AI导师通过提问引导你自主思考。

## 功能特点

- 🧠 **苏格拉底教学法**：不直接给出答案，通过问题引导自主思考
- 🎭 **个性化角色**：选择不同性格的AI导师（三月七、刻晴、苏格拉底等）
- 📚 **自定义教材**：上传任意教材内容，AI基于教材进行教学
- 🔧 **多模型支持**：支持OpenAI、Anthropic、阿里通义千问、智谱AI等多种LLM
- 💻 **本地部署**：完全本地运行，数据安全私密

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 初始化数据

```bash
python init_data.py
```

这会创建默认角色和示例教材。

### 3. 配置模型

启动服务后，访问 `http://localhost:8000/settings` 配置你的LLM API密钥。

### 4. 启动服务

```bash
python main.py
```

然后访问 http://localhost:8000

## 使用流程

1. **配置模型**：在设置页面添加你的LLM API密钥
2. **添加教材**：在教材管理页面添加你想要学习的内容
3. **选择角色**：选择一个你喜欢的AI导师
4. **开始学习**：创建新对话，与AI导师进行苏格拉底式对话

## 项目结构

```
cos2edu/
├── app/
│   ├── api/              # API路由
│   │   ├── routes.py     # 基础CRUD路由
│   │   ├── chat.py       # 聊天接口
│   │   └── pages.py      # 页面路由
│   ├── core/             # 核心配置
│   │   ├── config.py     # 配置管理
│   │   └── database.py   # 数据库模型
│   ├── schemas/          # Pydantic模型
│   └── services/         # 业务逻辑
│       ├── llm_providers.py   # LLM提供商
│       ├── crud_services.py   # CRUD服务
│       └── teaching_service.py # 教学逻辑
├── static/               # 前端静态文件
│   ├── index.html        # 首页
│   ├── chat.html         # 聊天界面
│   ├── characters.html   # 角色管理
│   ├── materials.html    # 教材管理
│   └── settings.html     # 设置页面
├── data/                 # 数据目录
├── main.py               # 应用入口
├── init_data.py          # 数据初始化
└── requirements.txt      # 依赖列表
```

## 支持的模型提供商

| 提供商 | 环境变量 | 常见模型 |
|--------|----------|----------|
| OpenAI | OPENAI_API_KEY | gpt-4o, gpt-3.5-turbo |
| Anthropic | ANTHROPIC_API_KEY | claude-3-5-sonnet-20241022 |
| 阿里通义千问 | DASHSCOPE_API_KEY | qwen-plus, qwen-max |
| 智谱AI | ZHIPU_API_KEY | glm-4, glm-3-turbo |

## 苏格拉底教学法

苏格拉底教学法的核心是**提问而非灌输**：

1. **不直接给出答案**：让学生自己推理
2. **循序渐进的问题**：从已知到未知
3. **关注推理过程**：答案不重要，思考过程才重要
4. **鼓励质疑精神**：培养批判性思维

## 参考

本项目参考了知乎文章《怎样用AI让自己沉迷学习？》中的教育理念。
