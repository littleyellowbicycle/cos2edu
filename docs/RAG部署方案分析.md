# RAG 部署方案分析

## 一、方案对比

### 1.1 开源 RAG 方案对比

| 方案 | 特点 | 镜像大小 | 内存需求 | 适用场景 |
|------|------|---------|---------|----------|
| **RAGFlow** | 微服务集群，功能完整 | ~10 GB | 8-16 GB | 企业级，高可用 |
| **MaxKB** | 完整包，中文友好 | ~5-8 GB | 4-8 GB | 企业内部知识库 |
| **LlamaIndex + Chroma** | 轻量灵活 | ~2-3 GB | 2-4 GB | 定制化，中小规模 |
| **LlamaIndex + FAISS** | 最小集 | ~1 GB | 1-2 GB | 快速起步，可扩展 |

### 1.2 最小化方案：LlamaIndex + FAISS

FAISS (Facebook AI Similarity Search) 是 Meta 开发的开源向量检索库：

| 特性 | 说明 |
|------|------|
| 向量索引 | 快速找到最相似的 K 个向量 |
| 近似搜索 | 节省计算资源 |
| 多种索引类型 | IVF、PQ、HNSW 等，平衡速度与精度 |
| 单进程库 | ~100MB，无需单独服务 |

### 1.3 RAGFlow 扩展能力

保留未来升级到 RAGFlow 的能力：

- RAGFlow 是完整 RAG 解决方案（文档上传、解析、分割、向量化、检索）
- 通过 API 对接：`/api/v1/datasets`, `/api/v1/chat/completions`
- 需要独立部署（8核16GB 服务器）

## 二、部署规模估算

### 2.1 cos2edu + RAGFlow 完整部署

| 组件 | 镜像大小 |
|------|---------|
| cos2edu backend | ~1.5 GB |
| cos2edu frontend (Nginx) | ~200 MB |
| Redis | ~150 MB |
| PostgreSQL | ~300 MB |
| RAGFlow (MySQL + MinIO + ES + Redis + core) | ~10 GB |
| **总计** | **~12-15 GB (仅镜像)** |

运行数据（ES 索引、MySQL、向量化数据）：10-50 GB

### 2.2 cos2edu + FAISS 最小集

| 组件 | 压缩后 | 解压运行 |
|------|-------|---------|
| Python 环境 (3.12-slim) | ~150 MB | ~500 MB |
| Python 依赖 | ~300 MB | ~800 MB |
| FAISS | ~150 MB | ~300 MB |
| Frontend (Nginx + 静态文件) | ~50 MB | ~150 MB |
| cos2edu 源码 | ~20 MB | ~50 MB |
| 向量索引数据 (示例教科书) | ~50 MB | ~50 MB |
| **总计** | **~720 MB** | **~1.9 GB** |

运行时内存：~1-2 GB

## 三、可扩展架构设计

### 3.1 分层架构

```
┌─────────────────────────────────────────────────────────┐
│                    前端 (静态文件)                       │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                   API 网关层 (可选)                      │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐                 │
│  │ Nginx   │  │ 直接访问 │  │ RAGFlow │                 │
│  │ 反向代理 │  │ FastAPI │  │ 代理    │                 │
│  └─────────┘  └─────────┘  └─────────┘                 │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                   核心层 (必选)                          │
│  FastAPI + Router + Service + Repository                │
└─────────────────────────────────────────────────────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   最小 RAG       │ │   RAGFlow Client │ │   完全自建 RAG   │
│  (FAISS/LlamaIdx)│ │   (扩展选项)     │ │  (Chroma/其他)   │
└─────────────────┘ └─────────────────┘ └─────────────────┘
              │             │             │
              └─────────────┼─────────────┘
                            ▼
┌─────────────────────────────────────────────────────────┐
│                   数据层                                  │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐                 │
│  │ SQLite  │  │ PostgreSQL │ │ 其他    │                 │
│  │ (开发/小型)│ │ (生产)   │ │         │                 │
│  └─────────┘  └─────────┘  └─────────┘                 │
└─────────────────────────────────────────────────────────┘
```

### 3.2 核心接口抽象

```python
# backend/app/services/base_rag.py
from abc import ABC, abstractmethod
from typing import List, Dict, Optional

class BaseRAGProvider(ABC):
    """RAG 提供者接口"""

    @abstractmethod
    async def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        """检索相关文本"""
        pass

    @abstractmethod
    async def add_documents(self, documents: List[Dict]) -> bool:
        """添加文档到知识库"""
        pass

# 最小集实现：LlamaIndex + FAISS
class SimpleRAGProvider(BaseRAGProvider):
    def __init__(self):
        from app.services.simple_rag import SimpleRAGService
        self._impl = SimpleRAGService()

    async def retrieve(self, query: str, top_k: int = 5):
        return await self._impl.retrieve(query, top_k)

# RAGFlow 扩展实现
class RAGFlowProvider(BaseRAGProvider):
    def __init__(self):
        self._config = {"url": "...", "api_key": "..."}

    async def retrieve(self, query: str, top_k: int = 5):
        # 调用 RAGFlow API
        pass
```

### 3.3 配置驱动切换

```python
# backend/app/core/config.py
from typing import Optional

class Settings(BaseSettings):
    # RAG 提供者: "simple" | "ragflow" | "chroma"
    RAG_PROVIDER: str = "simple"

    # RAGFlow 配置 (扩展时使用)
    RAGFLOW_URL: Optional[str] = None
    RAGFLOW_API_KEY: Optional[str] = None

    # 向量数据库配置
    VECTOR_DB_PATH: str = "./data/vectors"
```

### 3.4 Service 层动态选择

```python
# backend/app/services/rag_factory.py
from app.services.base_rag import BaseRAGProvider, SimpleRAGProvider, RAGFlowProvider

def get_rag_provider(provider: str = None) -> BaseRAGProvider:
    if provider is None:
        from app.core.config import settings
        provider = settings.RAG_PROVIDER

    providers = {
        "simple": SimpleRAGProvider,
        "ragflow": RAGFlowProvider,
        "chroma": ChromaRAGProvider,
    }
    return providers.get(provider, SimpleRAGProvider)()
```

## 四、打包方案

### 4.1 依赖分层

```
backend/
├── requirements-min.txt      # 最小集 (~300MB)
├── requirements-full.txt     # 完整集 (含 RAGFlow Client)
└── requirements-ragflow.txt   # RAGFlow 扩展
```

### 4.2 目录结构

```
cos2edu-min/
├── backend/
│   ├── app/
│   ├── requirements-min.txt
│   └── main.py
├── frontend/                   # 静态文件
├── data/                      # SQLite + 向量数据
├── docker-compose-min.yml     # 最小部署
└── README.md
```

### 4.3 文件大小

| 配置 | 压缩包 |
|------|--------|
| 最小集 | ~700 MB |
| + Nginx | +100 MB |
| + RAGFlow Client | +50 MB |
| 完整集 | ~900 MB |

## 五、扩展路径

### 5.1 当前：最小集 (FAISS)

```bash
# 启动最小集
docker-compose up -d backend
```

### 5.2 扩展 1：添加 Nginx

```bash
# 添加反向代理
cp docker-compose-min.yml docker-compose-full.yml
# 编辑添加 nginx 服务
docker-compose -f docker-compose-full.yml up -d
```

### 5.3 扩展 2：切换到 RAGFlow

```bash
# 配置环境变量
export RAG_PROVIDER=ragflow
export RAGFLOW_URL=http://ragflow:9380

# 启动 RAGFlow
docker-compose -f docker-compose-ragflow.yml up -d

# 重启后端
docker-compose restart backend
```

## 六、决策建议

### 6.1 推荐路线

**起步使用 LlamaIndex + FAISS**：
- 零部署复杂度
- ~1GB 可运行
- 保留扩展到 RAGFlow 的能力

### 6.2 升级时机

| 场景 | 升级到 RAGFlow |
|------|---------------|
| 向量数 > 100,000 | 是 |
| 需要可视化分割预览 | 是 |
| 需要多种文档格式解析 | 是 |
| 需要完整 RAG UI | 是 |
| 团队有 DevOps 能力 | 是 |

### 6.3 永不升级场景

- 个人/小团队运维能力有限
- 只需要简单文本检索
- 预算有限（服务器费用）

## 七、后续任务

- [ ] 实现 SimpleRAGProvider (LlamaIndex + FAISS)
- [ ] 实现 BaseRAGProvider 接口
- [ ] 配置驱动切换逻辑
- [ ] 测试最小集部署
- [ ] 文档化 RAGFlow 迁移步骤