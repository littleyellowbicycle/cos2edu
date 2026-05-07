# RAGFlow 集成方案

## 一、RAGFlow 简介

RAGFlow 是一款开源 RAG 引擎，特点：
- 完整 RAG 流程：上传 → 解析 → 分割 → 向量化 → 检索
- 多种文档支持：PDF、Word、Markdown、TXT 等
- 可视化分割预览
- 内置向量数据库（默认 SQLite）
- API 接口完备

---

## 二、部署方案

### 2.1 环境要求

| 组件 | 最低要求 | 推荐 |
|------|----------|------|
| CPU | 4 核 | 8 核 |
| 内存 | 8 GB | 16 GB |
| 磁盘 | 50 GB | 100 GB SSD |
| Docker | 24.x | 最新 |
| Docker Compose | 2.x | 最新 |

### 2.2 部署步骤

```bash
# 1. 克隆 RAGFlow
git clone https://github.com/infiniflow/ragflow.git
cd ragflow

# 2. 配置环境
cp .env.example .env
# 编辑 .env 设置 API_KEY 和相关配置

# 3. 启动服务
docker-compose up -d

# 4. 访问 Web UI
# http://your-server:9380
```

### 2.3 配置项

```env
# .env 配置
RAGFLOW_API_KEY=your-api-key
MYSQL_PASSWORD=your-mysql-password
LLM_PROVIDER=openai/anthropic/zhipu  # 选择 LLM 提供商
LLM_MODEL=gpt-4o/minimax-embed-text-v2  # 对应 Embedding 模型
```

---

## 三、教育场景适配

### 3.1 文档分割策略

RAGFlow 支持模板分割，教育场景建议：

| 模板名称 | 适用教材 | 分割逻辑 |
|----------|----------|----------|
| **教材模板** | 教科书、课件 | 按章节 → 按小节 → 按段落 |
| **问答模板** | 习题、试题 | 按题目单元 |
| **讲义模板** | 教案、笔记 | 按主题块 |

#### 3.1.1 分割参数

```json
{
  "chunk_size": 512,
  "chunk_overlap": 50,
  "parent_chunk_size": 2048,
  "auto_recognize": true,
  "delimiter": "\n\n## "
}
```

| 参数 | 说明 | 教育建议 |
|------|------|----------|
| chunk_size | 最小块大小 | 512 tokens，保留完整句子 |
| chunk_overlap | 块重叠 | 50 tokens，保持上下文 |
| parent_chunk_size | 父块大小 | 2048 tokens，保留完整概念 |
| delimiter | 分割符 | 按章节标题分割 |

### 3.2 元数据设计

教育场景需要额外元数据：

```json
{
  "title": "第三章：线性代数",
  "chapter": 3,
  "section": "3.1 矩阵运算",
  "difficulty": "intermediate",
  "prerequisites": ["第一章", "第二章"],
  "keywords": ["矩阵", "行列式", "线性方程组"],
  "course_type": "math"
}
```

### 3.3 检索策略

#### 3.3.1 混合检索

```json
{
  "search_method": "hybrid",
  "top_k": 5,
  "rerank": true,
  "rerank_top_k": 3
}
```

- **向量检索**：语义相似度匹配
- **关键词检索**：BM25 精确匹配
- **重排序**：综合相关性排序

#### 3.3.2 教育检索优化

```json
{
  "similarity_threshold": 0.5,
  "answer_prefix": "根据教材内容：",
  "prompt_template": "你是一位{difficulty}的{total_difficulty}教师，参考以下教材内容回答学生问题：\n{content}\n\n学生问题：{question}"
}
```

---

## 四、系统对接

### 4.1 对接架构

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   前端      │────▶│   后端      │────▶│  RAGFlow    │
│  (Vue)      │     │  (FastAPI)  │     │   API       │
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
                                              ▼
                                        ┌─────────────┐
                                        │  向量数据库  │
                                        │   (ES+MySQL)│
                                        └─────────────┘
```

### 4.2 RAGFlow API

#### 4.2.1 创建知识库

```python
import requests

RAGFLOW_URL = "http://your-ragflow:9380"
API_KEY = "your-api-key"

def create_dataset(name: str, description: str):
    """创建知识库"""
    response = requests.post(
        f"{RAGFLOW_URL}/api/v1/datasets",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={
            "name": name,
            "description": description,
            "embedding_model": "minimax-embed-text-v2"
        }
    )
    return response.json()
```

#### 4.2.2 上传文档

```python
def upload_document(dataset_id: str, file_path: str):
    """上传文档到知识库"""
    with open(file_path, 'rb') as f:
        response = requests.post(
            f"{RAGFLOW_URL}/api/v1/datasets/{dataset_id}/documents",
            headers={"Authorization": f"Bearer {API_KEY}"},
            files={"file": f}
        )
    return response.json()
```

#### 4.2.3 解析文档

```python
def parse_document(dataset_id: str, document_id: str):
    """触发文档解析"""
    response = requests.post(
        f"{RAGFLOW_URL}/api/v1/datasets/{dataset_id}/documents/{document_id}/parse",
        headers={"Authorization": f"Bearer {API_KEY}"}
    )
    return response.json()
```

#### 4.2.4 检索问答

```python
def chat(question: str, dataset_ids: list):
    """检索并生成回答"""
    response = requests.post(
        f"{RAGFLOW_URL}/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={
            "question": question,
            "dataset_ids": dataset_ids,
            "top_k": 5,
            "rerank": True
        }
    )
    return response.json()
```

### 4.3 后端服务封装

```python
# backend/app/services/ragflow_service.py

import requests
from typing import Optional, List, Dict
import os

class RAGFlowService:
    def __init__(self):
        self.base_url = os.getenv("RAGFLOW_URL", "http://localhost:9380")
        self.api_key = os.getenv("RAGFLOW_API_KEY")
        self.headers = {"Authorization": f"Bearer {self.api_key}"}

    def create_dataset(self, name: str, description: str = "") -> str:
        """创建知识库，返回 dataset_id"""
        response = requests.post(
            f"{self.base_url}/api/v1/datasets",
            headers=self.headers,
            json={
                "name": name,
                "description": description,
                "embedding_model": "minimax-embed-text-v2"
            }
        )
        data = response.json()
        return data["data"]["id"]

    def upload_document(self, dataset_id: str, file_path: str) -> str:
        """上传文档，返回 document_id"""
        with open(file_path, 'rb') as f:
            response = requests.post(
                f"{self.base_url}/api/v1/datasets/{dataset_id}/documents",
                headers=self.headers,
                files={"file": f}
            )
        data = response.json()
        return data["data"]["id"]

    def chat(self, question: str, dataset_ids: List[str]) -> Dict:
        """问答检索"""
        response = requests.post(
            f"{self.base_url}/api/v1/chat/completions",
            headers=self.headers,
            json={
                "question": question,
                "dataset_ids": dataset_ids,
                "top_k": 5,
                "rerank": True
            }
        )
        return response.json()

# 全局单例
ragflow_service = RAGFlowService()
```

### 4.4 对话接口集成

```python
# backend/app/api/v1/chat.py

@router.post("/{conversation_id}/stream")
async def chat_stream(
    request: Request,
    conversation_id: int,
    message: ChatMessage,
    model_config_id: Optional[int] = None,
):
    # ... 现有代码 ...
    
    # 如果有绑定教材，使用 RAG 检索
    if conversation.material and conversation.material.content_type == "ragflow":
        rag_result = ragflow_service.chat(
            question=message.content,
            dataset_ids=[conversation.material.ragflow_dataset_id]
        )
        # 将 RAG 检索结果注入上下文
        retrieved_content = rag_result["data"]["answer"]
    else:
        # 原有逻辑
        retrieved_content = None
    
    # ... 后续处理 ...
```

---

## 五、前端对接

### 5.1 教材管理页面改造

```
┌─────────────────────────────────────────────┐
│  教材管理                                   │
├─────────────────────────────────────────────┤
│                                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐    │
│  │ 文本输入 │  │ 网络链接 │  │ RAGFlow │    │
│  └─────────┘  └─────────┘  └─────────┘    │
│                                             │
│  [选择知识库 ▼]  [上传文档]  [解析状态 ✓]   │
│                                             │
└─────────────────────────────────────────────┘
```

### 5.2 内容类型选项

| 类型 | 说明 | 存储 |
|------|------|------|
| 文本 | 直接输入文本内容 | 数据库 content 字段 |
| 网络链接 | URL | 数据库 content_url 字段 |
| **RAGFlow** | 上传到 RAGFlow 知识库 | 数据库 ragflow_dataset_id |

### 5.3 前端状态

```javascript
// 前端表单
const form = ref({
  title: '',
  description: '',
  content_type: 'ragflow',  // 新增类型
  ragflow_dataset_id: '',   // RAGFlow 知识库 ID
  content: '',              // 仅文本类型使用
  content_url: ''           // 仅链接类型使用
})
```

---

## 六、数据模型

### 6.1 数据库扩展

```sql
-- materials 表新增字段
ALTER TABLE materials ADD COLUMN ragflow_dataset_id VARCHAR(100);
ALTER TABLE materials ADD COLUMN content_type VARCHAR(20) DEFAULT 'text';
-- content_type: 'text', 'url', 'ragflow'
```

### 6.2 Material 模型

```python
class Material(Base):
    __tablename__ = "materials"
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200))
    description = Column(Text)
    content_type = Column(String(20), default="text")  # text/url/ragflow
    # text 类型
    content = Column(Text)
    # url 类型
    content_url = Column(String(500))
    # ragflow 类型
    ragflow_dataset_id = Column(String(100))
    created_at = Column(DateTime)
```

---

## 七、部署清单

### 7.1 环境准备
- [ ] 服务器（建议 8 核 16GB）
- [ ] Docker + Docker Compose
- [ ] 域名（如需要外网访问）

### 7.2 RAGFlow 部署
- [ ] 克隆 RAGFlow 仓库
- [ ] 配置 .env 文件
- [ ] 启动 Docker 服务
- [ ] 验证 Web UI 访问

### 7.3 后端对接
- [ ] 安装 requests 库
- [ ] 配置 RAGFlow 连接信息
- [ ] 实现 RAGFlowService
- [ ] 集成到对话接口

### 7.4 前端改造
- [ ] 添加 RAGFlow 内容类型选项
- [ ] 知识库选择器
- [ ] 文档上传 UI
- [ ] 解析状态显示

### 7.5 测试验证
- [ ] 创建知识库
- [ ] 上传测试文档
- [ ] 配置分割模板
- [ ] 触发解析
- [ ] 对话测试

---

## 八、成本估算

### 8.1 自托管
| 资源 | 费用 |
|------|------|
| 服务器（8核16GB） | ~500元/月 |
| 存储（100GB） | ~30元/月 |
| LLM API 调用 | 按量计费 |

### 8.2 RAGFlow Cloud（可选）
| 套餐 | 价格 |
|------|------|
| 免费 | 3 个知识库，100MB |
| Pro | $99/月，无限知识库 |

---

## 九、后续任务

- [ ] 部署 RAGFlow 环境
- [ ] 配置 .env 和 LLM
- [ ] 后端集成 RAGFlow API
- [ ] 前端添加 RAGFlow 类型
- [ ] 教育分割模板配置
- [ ] 完整流程测试
