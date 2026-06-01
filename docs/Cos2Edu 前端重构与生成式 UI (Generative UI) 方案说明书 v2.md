# Cos2Edu 前端重构与生成式 UI (Generative UI) 方案说明书 v2

> 基于 v1 方案，结合 SillyTavern 参考案例进行进一步分析与细化。
> 日期：2026-06-01

---

## 1. 项目背景与目标

当前 cos2edu (苏格拉底式 AI 教学系统) 前端基于 Vue 3 手写构建，存在 UI 视觉陈旧、交互表现力不足的问题。为提升产品的教学沉浸感与用户体验，计划进行前端重构。

### 核心目标

1. **视觉与交互现代化**：引入现代设计系统，利用 AI 辅助工具（v0/Bolt等）快速重构 UI。
2. **实现运行时 Generative UI**：让 AI 在教学对话中动态渲染可交互组件（如情绪卡片、知识图谱、时间线），而非仅返回纯文本。
3. **支持桌面端封装**：重构后的前端需无缝支持打包为轻量级桌面应用。

---

## 2. SillyTavern 参考案例分析

### 2.1 SillyTavern 是什么

SillyTavern 是一个面向高级用户的 LLM 前端界面，始于 2023 年 2 月（TavernAI 1.2.8 的 fork），至今已有 300+ 贡献者和 3 年独立开发。它提供：

- 统一的多 LLM API 接入层（OpenAI/Claude/本地模型等 20+ 后端）
- 角色卡片系统（PNG 元数据嵌入，V2/V3 规范）
- WorldInfo/Lorebook 动态知识注入
- 扩展系统（manifest.json + 事件钩子 + getContext API）
- 表情/场景/Live2D 多模态渲染
- STscript 脚本引擎

### 2.2 与 Cos2Edu 的功能映射

| SillyTavern 功能 | Cos2Edu 对应 | 差异点 |
|-----------------|-------------|--------|
| 角色卡片 (Character Card) | 角色系统 (Character) | ST 用 PNG 嵌入数据，Cos2Edu 用数据库+API；Cos2Edu 角色有情感引擎和教学风格 |
| WorldInfo / Lorebook | 知识图谱 + RAG | ST 用关键词触发注入，Cos2Edu 用向量检索+依赖DAG |
| 表情系统 (Sprites/Expressions) | 情感引擎 (EmotionEngine) | ST 用静态图片切换，Cos2Edu 需要连续情感值+动态表情 |
| 场景背景 (Backgrounds) | 场景系统 (SceneEngine) | ST 手动/脚本切换，Cos2Edu 由叙事引擎自动触发 |
| 扩展系统 (Extensions) | **Generative UI 组件** | ST 扩展是用户安装的静态功能，Cos2Edu 的 Generative 组件由 AI 动态触发 |
| STscript 脚本 | 无直接对应 | Cos2Edu 的"脚本"是 LLM Function Calling，由 AI 决策而非用户编写 |
| Quick Reply / Buttons | 测验表单 (QuizForm) | ST 是预设快捷回复，Cos2Edu 是 AI 生成的交互式测验 |

### 2.3 SillyTavern 架构的关键启示

#### 启示 1：扩展系统 = 组件注册表

SillyTavern 的扩展系统通过 `manifest.json` 声明元数据，通过 `getContext()` 访问全局状态，通过事件钩子 (`eventSource.on`) 响应系统事件。这与 Cos2Edu 的 Generative UI 组件映射表高度相似：

```
SillyTavern Extension          Cos2Edu Generative Component
─────────────────────          ──────────────────────────────
manifest.json 声明             ComponentRegistry 注册
getContext() 访问状态          useNarrativeStore() 访问状态
eventSource.on() 监听事件      WebSocket on('ui.render') 监听
renderExtensionTemplateAsync()  <DynamicComponent /> 渲染
extensionSettings 持久化       组件 props 由后端推送
```

**借鉴点**：Cos2Edu 的 Generative 组件应采用类似的注册-发现-渲染模式，而非硬编码映射表。

#### 启示 2：WorldInfo 的动态注入机制

SillyTavern 的 WorldInfo/Lorebook 系统根据对话上下文动态注入知识条目：
- 每个条目有触发关键词 (`keys`)
- 根据相关性评分 (`calculateRelevanceScore`) 排序
- 有预算控制 (`world_info_budget`) 限制注入量
- 支持深度控制 (`world_info_depth`) 管理搜索范围

**借鉴点**：Cos2Edu 的 Context Budget 机制与 ST 的 WorldInfo 预算控制本质相同，但 Cos2Edu 还需要考虑知识依赖关系（DAG），比 ST 的关键词触发更复杂。

#### 启示 3：事件驱动的 UI 更新

SillyTavern 定义了完整的事件类型体系：
- 应用生命周期：`APP_INITIALIZED`, `APP_READY`
- 消息事件：`MESSAGE_RECEIVED`, `CHARACTER_MESSAGE_RENDERED`
- 生成事件：`GENERATION_STARTED`, `GENERATION_ENDED`
- 角色事件：`CHARACTER_EDITED`, `CHARACTER_DELETED`

**借鉴点**：Cos2Edu 的 WebSocket 消息协议应定义同样完整的事件类型，特别是区分"消息生成中"和"消息已渲染"两个阶段——Generative UI 组件应在消息渲染后插入，而非在文本流中。

#### 启示 4：角色卡片的可分享性

SillyTavern 通过 PNG 元数据嵌入实现了"一张图片就是一个角色"的可分享性。这是社区生态繁荣的关键。

**借鉴点**：Cos2Edu 的角色配置（性格、情感配置、教学风格）应支持导入导出，但不一定用 PNG 嵌入。JSON/YAML 导出更符合教育场景。

---

## 3. 整体架构设计（细化版）

基于现有后端资产与桌面端需求，确立 **"FastAPI 后端主导 + Vue 3 前端渲染 + Tauri 桌面容器"** 的架构。

> **v2 变更**：v1 方案建议从 Vue 3 切换到 React，但经过进一步分析，**保持 Vue 3 技术栈**更为合理，原因见 3.1 节。

### 3.1 技术栈决策：保持 Vue 3

| 考量因素 | 切换 React | 保持 Vue 3 |
|---------|-----------|-----------|
| 现有代码资产 | 全部重写（14个视图+store+composable） | 零迁移成本 |
| Generative UI 能力 | React 有 Vercel AI SDK | Vue 3 `<component :is>` + `defineAsyncComponent` 同样支持 |
| 团队熟悉度 | 需要重新学习 | 已有积累 |
| SillyTavern 参考价值 | ST 本身不用 React，扩展支持 React 是可选的 | 无差异 |
| Tauri 兼容性 | 完全兼容 | 完全兼容 |
| 社区生态 | 更大 | 足够大 |

**结论**：Vue 3 的 `<component :is="componentName" v-bind="props" />` 天然支持动态组件渲染，与 React 的 `ComponentMap` 模式等价。无需为 Generative UI 切换技术栈。

### 3.2 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    桌面端容器 (Tauri)                         │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │            前端渲染层 (Vue 3 + Vite)                   │  │
│  │                                                       │  │
│  │  ┌─────────────────┐  ┌──────────────────────────┐   │  │
│  │  │  Narrative Store │  │  Component Registry      │   │  │
│  │  │  (Pinia)         │  │  (Generative 组件注册表)  │   │  │
│  │  └────────┬────────┘  └────────────┬─────────────┘   │  │
│  │           │                        │                  │  │
│  │  ┌────────▼────────────────────────▼──────────────┐  │  │
│  │  │          Dynamic Renderer                      │  │  │
│  │  │  <component :is="name" v-bind="props" />       │  │  │
│  │  │  + 生命周期管理 + 懒加载 + 错误边界             │  │  │
│  │  └───────────────────────┬────────────────────────┘  │  │
│  │                          │                            │  │
│  │  ┌───────────────────────▼────────────────────────┐  │  │
│  │  │          WebSocket Client                      │  │  │
│  │  │  事件分发器 + 重连对账 + 消息缓冲              │  │  │
│  │  └───────────────────────┬────────────────────────┘  │  │
│  └──────────────────────────┼───────────────────────────┘  │
│                             │ WS / HTTP                     │
│  ┌──────────────────────────▼───────────────────────────┐  │
│  │            后端服务层 (FastAPI)                        │  │
│  │                                                       │  │
│  │  ┌─────────────────────────────────────────────────┐ │  │
│  │  │  UI Orchestrator (新增)                         │ │  │
│  │  │  - LLM Function Calling 工具定义               │ │  │
│  │  │  - tool_call → UI JSON 转换                    │ │  │
│  │  │  - 组件推送调度 (与文本流协调)                  │ │  │
│  │  └───────────────────────┬─────────────────────────┘ │  │
│  │                          │                            │  │
│  │  ┌───────────────────────▼─────────────────────────┐ │  │
│  │  │  Narrative Engine (叙事/教学引擎)                │ │  │
│  │  │  - WorldState / Character / Event / Emotion     │ │  │
│  │  │  - Teaching / Assessment Engines                │ │  │
│  │  └───────────────────────┬─────────────────────────┘ │  │
│  │                          │                            │  │
│  │  ┌───────────────────────▼─────────────────────────┐ │  │
│  │  │  WebSocket Server                               │ │  │
│  │  │  - 消息类型路由                                 │ │  │
│  │  │  - 流式文本推送                                 │ │  │
│  │  │  - UI 指令推送                                  │ │  │
│  │  └─────────────────────────────────────────────────┘ │  │
│  └──────────────────────────┬───────────────────────────┘  │
│                             │ API Call                       │
│  ┌──────────────────────────▼───────────────────────────┐  │
│  │            大语言模型 (GPT-4o / 通义等)                │  │
│  │  - 理解意图                                           │  │
│  │  - 触发 Function Calling (决定调用哪个前端组件)        │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. 核心机制：Generative UI 实现方案（细化版）

### 4.1 三层角色模型（不变，细化职责）

| 角色 | 职责 | SillyTavern 对应 |
|------|------|-----------------|
| **LLM (决策者)** | 根据上下文判断何时展示组件，返回 tool_calls | 无直接对应（ST 无 AI 驱动 UI） |
| **FastAPI (翻译官)** | 定义工具 Schema → 拦截 tool_calls → 转换为 UI JSON → 推送 | ST 的 `getContext()` + 事件系统 |
| **Vue 3 (渲染器)** | 解析 UI JSON → 查找组件 → 动态渲染 | ST 的 Extension 渲染机制 |

### 4.2 UI JSON 协议规范（细化）

借鉴 SillyTavern 扩展系统的 manifest.json 设计，UI JSON 协议需支持：

```jsonc
// WebSocket 推送的消息格式
{
  "type": "ui.render",
  "id": "msg_uuid_123",
  "timestamp": "2026-06-01T10:30:00Z",
  "components": [
    {
      "id": "comp_1",
      "component": "EmotionCard",
      "version": "1.0",
      "props": {
        "mood": "sad",
        "trust": 0.8,
        "characterName": "甘雨"
      },
      "slot": "inline",
      "position": "after_text",
      "lifecycle": "persistent"
    },
    {
      "id": "comp_2",
      "component": "Timeline",
      "version": "1.0",
      "props": {
        "events": [
          { "year": -399, "label": "苏格拉底受审" },
          { "year": -399, "label": "饮鸩而亡" }
        ]
      },
      "slot": "sidebar",
      "position": "replace",
      "lifecycle": "ephemeral"
    }
  ],
  "metadata": {
    "trigger": "function_call",
    "tool_name": "show_emotion_card",
    "confidence": 0.95
  }
}
```

**协议字段说明**：

| 字段 | 类型 | 说明 | 借鉴来源 |
|------|------|------|---------|
| `component` | string | 组件注册名 | ST manifest.json 的 `js` 字段 |
| `version` | string | 组件版本，用于兼容性检查 | ST manifest.json 的 `version` |
| `props` | object | 组件属性 | ST `renderExtensionTemplateAsync` 的 data 参数 |
| `slot` | enum | 渲染位置：`inline`(消息内) / `sidebar`(侧边栏) / `overlay`(浮层) / `panel`(独立面板) | ST 扩展的 DOM 挂载点选择 |
| `position` | enum | 插入方式：`after_text`(文本后) / `before_text`(文本前) / `replace`(替换) | 无对应，Cos2Edu 新增 |
| `lifecycle` | enum | 生命周期：`persistent`(持久) / `ephemeral`(随消息消失) / `sticky`(置顶直到替换) | ST `extensionSettings` 的持久化概念 |
| `metadata` | object | 扩展元数据，预留字段 | ST manifest.json 的 `i18n`/`auto_update` |

### 4.3 组件注册表设计（借鉴 ST 扩展系统）

SillyTavern 的扩展通过 manifest.json 声明式注册。Cos2Edu 的 Generative 组件采用类似的注册机制：

```typescript
// frontend/src/components/generative/registry.ts

interface GenerativeComponentMeta {
  name: string
  version: string
  description: string
  propsSchema: Record<string, PropDefinition>
  slot: 'inline' | 'sidebar' | 'overlay' | 'panel'
  defaultLifecycle: 'persistent' | 'ephemeral' | 'sticky'
  loader: () => Promise<any>
}

const registry = new Map<string, GenerativeComponentMeta>()

export function registerComponent(meta: GenerativeComponentMeta) {
  registry.set(meta.name, meta)
}

export function getComponent(name: string): GenerativeComponentMeta | undefined {
  return registry.get(name)
}

export function validateProps(name: string, props: Record<string, any>): boolean {
  const meta = registry.get(name)
  if (!meta) return false
  // 根据 propsSchema 校验
  return true
}
```

```typescript
// frontend/src/components/generative/index.ts

import { registerComponent } from './registry'

registerComponent({
  name: 'EmotionCard',
  version: '1.0',
  description: '角色情绪状态卡片',
  propsSchema: {
    mood: { type: 'string', required: true, enum: ['happy', 'sad', 'neutral', 'angry', 'curious'] },
    trust: { type: 'number', required: true, min: 0, max: 1 },
    characterName: { type: 'string', required: true },
  },
  slot: 'inline',
  defaultLifecycle: 'persistent',
  loader: () => import('./EmotionCard.vue'),
})

registerComponent({
  name: 'Timeline',
  version: '1.0',
  description: '历史事件时间线',
  propsSchema: {
    events: { type: 'array', required: true },
  },
  slot: 'sidebar',
  defaultLifecycle: 'sticky',
  loader: () => import('./Timeline.vue'),
})

registerComponent({
  name: 'QuizForm',
  version: '1.0',
  description: '交互式测验表单',
  propsSchema: {
    pointId: { type: 'string', required: true },
    questions: { type: 'array', required: true },
  },
  slot: 'inline',
  defaultLifecycle: 'ephemeral',
  loader: () => import('./QuizForm.vue'),
})

registerComponent({
  name: 'KnowledgeGraph',
  version: '1.0',
  description: '知识点依赖关系图',
  propsSchema: {
    nodes: { type: 'array', required: true },
    edges: { type: 'array', required: true },
    highlight: { type: 'string', required: false },
  },
  slot: 'panel',
  defaultLifecycle: 'sticky',
  loader: () => import('./KnowledgeGraph.vue'),
})

registerComponent({
  name: 'SceneCard',
  version: '1.0',
  description: '场景切换卡片（借鉴 ST 背景系统）',
  propsSchema: {
    sceneId: { type: 'string', required: true },
    sceneName: { type: 'string', required: true },
    description: { type: 'string', required: false },
    backgroundImage: { type: 'string', required: false },
  },
  slot: 'overlay',
  defaultLifecycle: 'ephemeral',
  loader: () => import('./SceneCard.vue'),
})
```

### 4.4 动态渲染器（借鉴 ST 的事件驱动模式）

SillyTavern 通过 `eventSource.on(eventType, handler)` 监听事件并触发 UI 更新。Cos2Edu 的渲染器采用类似模式：

```vue
<!-- frontend/src/components/generative/DynamicRenderer.vue -->
<template>
  <div class="generative-slot" :class="`slot-${slot}`">
    <component
      v-for="item in activeComponents"
      :key="item.id"
      :is="item.resolved"
      v-bind="item.props"
      @destroy="removeComponent(item.id)"
    />
    <div v-if="loadingComponents.length > 0" class="component-loader">
      <div class="loader-spinner"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, defineAsyncComponent, onMounted, onUnmounted } from 'vue'
import { useWebSocket } from '@/composables/useWebSocket'
import { getComponent, validateProps } from './registry'

const props = defineProps({
  slot: { type: String, required: true },
})

const ws = useWebSocket()
const components = ref([])

const activeComponents = computed(() =>
  components.value.filter(c => c.resolved !== null)
)

const loadingComponents = computed(() =>
  components.value.filter(c => c.resolved === null)
)

function handleUIRender(msg) {
  if (msg.type !== 'ui.render') return

  for (const comp of msg.components) {
    if (comp.slot !== props.slot) continue
    if (!validateProps(comp.component, comp.props)) {
      console.warn(`Invalid props for ${comp.component}`)
      continue
    }

    const meta = getComponent(comp.component)
    if (!meta) {
      console.warn(`Unknown component: ${comp.component}`)
      continue
    }

    const asyncComp = defineAsyncComponent({
      loader: meta.loader,
      loadingComponent: LoadingPlaceholder,
      errorComponent: ErrorFallback,
      delay: 100,
      timeout: 5000,
    })

    components.value.push({
      id: comp.id,
      name: comp.component,
      props: comp.props,
      lifecycle: comp.lifecycle || meta.defaultLifecycle,
      resolved: asyncComp,
    })
  }
}

function removeComponent(id) {
  components.value = components.value.filter(c => c.id !== id)
}

let unsubscribe
onMounted(() => {
  unsubscribe = ws.on('ui.render', handleUIRender)
})

onUnmounted(() => {
  if (unsubscribe) unsubscribe()
})
</script>
```

### 4.5 交互时序（细化版，含组件生命周期）

```
用户输入 "苏格拉底怎么死的"
    │
    ▼
[1] Vue → WS → FastAPI: { type: "chat.send", payload: { content: "..." } }
    │
    ▼
[2] FastAPI → LLM: 携带 tools + 对话上下文
    │
    ▼
[3] LLM 返回: 文本流 + tool_calls
    │
    ├── 文本流 → WS 推送 { type: "chat.stream", content: "苏格拉底在公元前399年..." }
    │
    └── tool_calls → UI Orchestrator 处理
         │
         ├── tool_call: show_emotion_card(mood="sad", trust=0.8)
         │   → 转换为 UI JSON: { component: "EmotionCard", props: {...}, slot: "inline" }
         │
         └── tool_call: show_timeline(events=[...])
             → 转换为 UI JSON: { component: "Timeline", props: {...}, slot: "sidebar" }
    │
    ▼
[4] FastAPI → WS 推送:
    { type: "ui.render", components: [EmotionCard, Timeline] }
    │
    ▼
[5] Vue DynamicRenderer 接收:
    ├── inline slot → 渲染 EmotionCard（消息气泡内）
    └── sidebar slot → 渲染 Timeline（侧边栏）
    │
    ▼
[6] 用户与 QuizForm 交互（如点击选项）
    → Vue → WS → FastAPI: { type: "ui.interact", componentId: "comp_2", action: "select", value: "..." }
    │
    ▼
[7] FastAPI → LLM: 根据交互结果继续对话
```

### 4.6 后端 UI Orchestrator 设计

```python
# backend/app/engines/ui_orchestrator.py

from pydantic import BaseModel
from typing import Optional
from enum import Enum

class ComponentSlot(str, Enum):
    INLINE = "inline"
    SIDEBAR = "sidebar"
    OVERLAY = "overlay"
    PANEL = "panel"

class ComponentLifecycle(str, Enum):
    PERSISTENT = "persistent"
    EPHEMERAL = "ephemeral"
    STICKY = "sticky"

class UIComponent(BaseModel):
    id: str
    component: str
    version: str = "1.0"
    props: dict
    slot: ComponentSlot = ComponentSlot.INLINE
    position: str = "after_text"
    lifecycle: ComponentLifecycle = ComponentLifecycle.EPHEMERAL

class UIOrchestrator:
    TOOL_DEFINITIONS = [
        {
            "type": "function",
            "function": {
                "name": "show_emotion_card",
                "description": "当角色情绪发生显著变化时展示情绪状态卡片",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "mood": {
                            "type": "string",
                            "enum": ["happy", "sad", "neutral", "angry", "curious", "worried", "proud"],
                            "description": "角色当前情绪"
                        },
                        "trust": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1,
                            "description": "角色对学生的信任度"
                        },
                        "reason": {
                            "type": "string",
                            "description": "情绪变化的原因（简要）"
                        }
                    },
                    "required": ["mood", "trust"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "show_timeline",
                "description": "当讨论历史事件或时间相关内容时展示时间线",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "events": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "year": {"type": "number"},
                                    "label": {"type": "string"}
                                },
                                "required": ["year", "label"]
                            },
                            "description": "时间线事件列表"
                        },
                        "title": {"type": "string", "description": "时间线标题"}
                    },
                    "required": ["events"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "show_quiz",
                "description": "当需要检验学生理解时展示测验表单",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "point_id": {"type": "string", "description": "知识点ID"},
                        "question_type": {
                            "type": "string",
                            "enum": ["choice", "short_answer", "true_false"],
                            "description": "题目类型"
                        },
                        "question": {"type": "string", "description": "题目内容"},
                        "options": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "选项（仅选择题需要）"
                        }
                    },
                    "required": ["point_id", "question_type", "question"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "show_knowledge_graph",
                "description": "当需要展示知识点之间的依赖关系时展示知识图谱",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "highlight": {"type": "string", "description": "高亮的知识点ID"},
                        "depth": {"type": "integer", "description": "展示的依赖深度", "default": 2}
                    },
                    "required": ["highlight"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "switch_scene",
                "description": "当叙事场景发生变化时切换场景",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "scene_id": {"type": "string", "description": "场景ID"},
                        "transition": {
                            "type": "string",
                            "enum": ["fade", "slide", "instant"],
                            "description": "过渡效果",
                            "default": "fade"
                        }
                    },
                    "required": ["scene_id"]
                }
            }
        }
    ]

    TOOL_TO_COMPONENT = {
        "show_emotion_card": ("EmotionCard", ComponentSlot.INLINE, ComponentLifecycle.PERSISTENT),
        "show_timeline": ("Timeline", ComponentSlot.SIDEBAR, ComponentLifecycle.STICKY),
        "show_quiz": ("QuizForm", ComponentSlot.INLINE, ComponentLifecycle.EPHEMERAL),
        "show_knowledge_graph": ("KnowledgeGraph", ComponentSlot.PANEL, ComponentLifecycle.STICKY),
        "switch_scene": ("SceneCard", ComponentSlot.OVERLAY, ComponentLifecycle.EPHEMERAL),
    }

    def convert_tool_calls(self, tool_calls: list) -> list[UIComponent]:
        components = []
        for tc in tool_calls:
            func_name = tc.function.name
            if func_name not in self.TOOL_TO_COMPONENT:
                continue

            comp_name, slot, lifecycle = self.TOOL_TO_COMPONENT[func_name]
            import json
            args = json.loads(tc.function.arguments)

            components.append(UIComponent(
                id=f"comp_{tc.id}",
                component=comp_name,
                props=args,
                slot=slot,
                lifecycle=lifecycle,
            ))

        return components
```

---

## 5. 借鉴 SillyTavern 的关键设计模式

### 5.1 事件驱动架构

SillyTavern 的核心是事件总线 (`eventSource`)。Cos2Edu 的 WebSocket 消息协议应采用相同模式：

```typescript
// 扩展 useWebSocket.js 的事件类型定义
enum WSEventType {
  // 应用生命周期
  APP_READY = 'app.ready',

  // 聊天消息
  CHAT_STREAM = 'chat.stream',
  CHAT_COMPLETE = 'chat.complete',
  MESSAGE_RECEIVED = 'chat.message_received',

  // UI 渲染（核心）
  UI_RENDER = 'ui.render',
  UI_DESTROY = 'ui.destroy',
  UI_UPDATE = 'ui.update',

  // 叙事事件
  SCENE_SWITCH = 'scene.switch',
  EMOTION_CHANGE = 'emotion.change',
  TIME_ADVANCE = 'time.advance',

  // 状态同步
  STATE_SYNC = 'state.sync',
  STATE_DELTA = 'state.delta',
}
```

### 5.2 Context Budget（借鉴 ST WorldInfo 预算）

SillyTavern 的 WorldInfo 系统通过 `world_info_budget` 和 `world_info_depth` 控制注入量。Cos2Edu 的 Context Budget 更复杂，需要同时管理：

| 维度 | SillyTavern | Cos2Edu |
|------|------------|---------|
| 预算单位 | 条目数量 | Token 数量 |
| 检索方式 | 关键词匹配 | 向量相似度 + DAG 依赖 |
| 优先级 | 手动权重 | 知识点难度 + 学习进度 + 依赖关系 |
| 深度控制 | 历史对话轮数 | DAG 依赖深度 |

### 5.3 角色状态持久化（借鉴 ST Character Card Extensions）

SillyTavern 在角色卡片的 `extensions` 字段中存储扩展数据。Cos2Edu 的角色状态（情感值、信任度、教学进度）应采用类似的分层持久化：

```
Critical (立即写DB):  情感值、信任度、学习进度
Soft (定时批量写):    角色心情描述、对话摘要
Ephemeral (仅内存):   当前对话上下文、临时表情
```

---

## 6. 桌面端封装策略：Tauri 优先（不变）

### 6.1 推荐架构

采用 Tauri + Vite + Vue 3。Tauri 仅作为轻量级壳子提供系统级 API（文件读写、窗口控制等），业务逻辑依然由内嵌的 FastAPI 或远程服务提供。

### 6.2 Tauri 与 SillyTavern 的部署差异

| 维度 | SillyTavern | Cos2Edu (Tauri) |
|------|------------|-----------------|
| 运行方式 | Node.js 服务器 + 浏览器 | Tauri 壳 + WebView |
| 后端 | Express.js (同进程) | FastAPI (子进程) |
| 数据存储 | 文件系统 (JSON/JSONL) | SQLite + YAML |
| 分发方式 | git clone + npm start | 安装包 (.msi / .dmg) |

---

## 7. 实施路线图（细化版）

### 阶段一：Generative UI 基础设施 (1 周)

- [ ] 实现组件注册表 (`registry.ts`)
- [ ] 实现 DynamicRenderer 组件
- [ ] 扩展 WebSocket 协议，增加 `ui.render` / `ui.destroy` / `ui.update` 消息类型
- [ ] 后端实现 UIOrchestrator（工具定义 + tool_call 转换）
- [ ] 实现 EmotionCard 作为第一个 Generative 组件（端到端验证）

### 阶段二：核心 Generative 组件开发 (2 周)

- [ ] EmotionCard：角色情绪可视化（借鉴 ST 表情系统，但用连续值而非离散图片）
- [ ] QuizForm：交互式测验（借鉴 ST Quick Reply 的按钮交互模式）
- [ ] Timeline：历史事件时间线
- [ ] KnowledgeGraph：知识点依赖关系图（DAG 可视化）
- [ ] SceneCard：场景切换过渡（借鉴 ST 背景切换系统）

### 阶段三：UI 现代化重构 (2 周)

- [ ] 引入 TailwindCSS，替换当前手写 CSS
- [ ] 利用 v0.dev / Bolt.new 重新生成核心页面布局
- [ ] Chat 页面重构：集成 DynamicRenderer 的 inline/sidebar/overlay slot
- [ ] Curriculum 页面重构：集成 KnowledgeGraph 组件
- [ ] Characters 页面重构：集成 EmotionCard 组件

### 阶段四：桌面端封装 (1 周)

- [ ] 引入 Tauri，配置应用图标、窗口属性
- [ ] 通过 Tauri Commands 暴露本地文件操作等系统 API
- [ ] 处理前端与本地 FastAPI 子进程的启动与联调
- [ ] 打包测试 (Windows .msi)

### 阶段五：优化与迭代

- [ ] LLM Prompt 调优，提高 Function Calling 准确率
- [ ] 组件交互深化（知识图谱缩放拖拽、测验结果动画）
- [ ] 桌面端离线缓存与异常处理
- [ ] 组件版本管理与向后兼容

---

## 8. 风险与应对（细化版）

| 风险点 | 影响 | 应对策略 | SillyTavern 参考 |
|--------|------|---------|-----------------|
| LLM 未按预期调用工具 | 未能触发 Generative UI，仅返回文本 | 优化 System Prompt；后端兜底逻辑：纯文本包裹为默认气泡组件 | ST 无 AI 驱动 UI，不存在此问题 |
| 动态组件渲染性能 | 频繁装卸复杂组件导致卡顿 | `defineAsyncComponent` 懒加载；key 控制复用；限制单次组件数量 ≤ 3 | ST 扩展的 `loading_order` 控制加载顺序 |
| UI JSON 协议扩展性差 | 后期新增组件修改成本高 | `metadata` 预留字段；工厂模式解耦；组件版本号 | ST manifest.json 的 `version` + `auto_update` |
| Tauri 跨平台 WebView 差异 | Windows/Mac CSS 渲染差异 | TailwindCSS 标准类；强制 WebView 版本 | ST 无桌面端封装 |
| 组件 props 校验失败 | 渲染错误或 XSS | 后端 Pydantic 校验 + 前端 propsSchema 校验 + 错误边界 | ST 的 DOMPurify HTML 清洗 |
| WebSocket 断连导致 UI 状态丢失 | 组件消失或重复渲染 | 重连对账机制；组件 ID 去重；lifecycle 标记持久组件 | ST 无 WS，但扩展有 `onEnable`/`onDisable` 钩子 |

---

## 9. 与 v1 方案的关键差异总结

| 维度 | v1 方案 | v2 方案（本文档） | 变更原因 |
|------|--------|-----------------|---------|
| 前端框架 | React + TypeScript | **Vue 3 + TypeScript** | 现有代码资产 + Vue 动态组件能力足够 |
| 组件映射 | 硬编码 ComponentMap | **注册表模式 (registry)** | 借鉴 ST manifest.json，支持动态发现和版本管理 |
| UI JSON 协议 | 简单的 component + props | **增加 slot/position/lifecycle/version/metadata** | 借鉴 ST 扩展系统的声明式设计 |
| 渲染位置 | 仅消息内 | **inline/sidebar/overlay/panel 四种 slot** | 借鉴 ST 扩展的多挂载点设计 |
| 组件生命周期 | 无 | **persistent/ephemeral/sticky** | 借鉴 ST 扩展的启用/禁用机制 |
| 事件系统 | 简单 WS 消息 | **完整事件类型体系** | 借鉴 ST eventSource 的类型化事件 |
| 实施顺序 | 先切换 React → 再做 Generative UI | **先做 Generative UI 基础设施 → 再 UI 现代化** | 降低风险，渐进式改进 |

---

## 10. 渲染管线深度分析：Markdown 层 vs Generative 层

### 10.1 问题的提出

LLM 的输出是自由的——可能包含表格、代码块、列表、数学公式、emoji 标题、分节内容等。一个关键问题自然浮现：**预注册的 Generative 组件能覆盖 LLM 输出的所有形式吗？**

答案是：**不需要覆盖**。因为 LLM 的输出实际上分为两个本质不同的层次，需要两套独立的渲染管线分别处理。

### 10.2 两层渲染管线模型

LLM 的输出可以拆分为两个层次：

```
第一层：富文本内容（Markdown 渲染层）
├── 普通文本
├── 表格（GFM Table）
├── 代码块（语法高亮）
├── 数学公式（KaTeX）
├── 列表（有序/无序）
├── 图片链接
├── Mermaid 图表
└── 标题/分割线/引用

第二层：交互式组件（Generative UI 层）
├── EmotionCard（情绪卡片 — 可视化角色情感状态）
├── QuizForm（测验表单 — 可填写、可提交）
├── Timeline（时间线 — 可交互的历史事件轴）
├── KnowledgeGraph（知识图谱 — 可缩放拖拽的 DAG）
└── SceneCard（场景切换 — 带过渡动画的场景卡片）
```

**区分原则**：

- 如果一个内容只需要 **"看"**，放 Markdown 层
- 如果一个内容需要 **"点/拖/填/提交"**，放 Generative 层

### 10.3 完整的三层渲染架构

```
┌─────────────────────────────────────────────────────────┐
│               LLM 输出（自由文本 + tool_calls）           │
│                                                         │
│  "苏格拉底的主要观点如下：                                 │
│                                                         │
│   | 观点 | 说明 |                                        │
│   |------|------|                                       │
│   | 产婆术 | 通过提问引导思考 |                             │
│   | 灵魂不朽 | 死亡是灵魂的解脱 |                           │
│                                                         │
│   [tool_call: show_emotion_card(mood='proud', trust=0.7)]│
│   [tool_call: show_timeline(events=[...])]               │
│  "                                                      │
└──────────────────────────┬──────────────────────────────┘
                           │
                    后端拆分为两部分
                           │
           ┌───────────────┴───────────────┐
           ▼                               ▼
    ┌──────────────┐              ┌──────────────┐
    │  文本部分     │              │  tool_calls   │
    │  (Markdown)  │              │  (结构化数据)  │
    └──────┬───────┘              └──────┬───────┘
           │                             │
           ▼                             ▼
    ┌──────────────┐              ┌──────────────┐
    │  第一层渲染   │              │  第二层渲染   │
    │  Markdown    │              │  Generative  │
    │  Renderer    │              │  Components  │
    │              │              │  (预注册)     │
    │  处理：       │              │              │
    │  · 文本      │              │  · EmotionCard│
    │  · 表格 ✅   │              │  · Timeline   │
    │  · 代码块 ✅ │              │  · QuizForm   │
    │  · 列表 ✅   │              │  · Knowledge  │
    │  · 数学公式 ✅│              │    Graph      │
    │  · 图片 ✅   │              │  · SceneCard  │
    │  · Mermaid ✅│              │              │
    └──────┬───────┘              └──────┬───────┘
           │                             │
           ▼                             ▼
    ┌──────────────────────────────────────────┐
    │           第三层：组合渲染                  │
    │                                          │
    │  <MessageBubble>                         │
    │    <MarkdownContent :html="..." />       │
    │    <DynamicRenderer slot="inline">       │
    │      <EmotionCard />                     │
    │    </DynamicRenderer>                    │
    │  </MessageBubble>                        │
    │                                          │
    │  <Sidebar>                               │
    │    <DynamicRenderer slot="sidebar">      │
    │      <Timeline />                        │
    │    </DynamicRenderer>                    │
    │  </Sidebar>                              │
    └──────────────────────────────────────────┘
```

### 10.4 Markdown 层 vs Generative 层的能力边界

| 内容类型 | Markdown 能力 | 是否需要 Generative 组件 | 说明 |
|---------|-------------|----------------------|------|
| 简单表格 | ✅ GFM 表格 | ❌ | `marked` 原生支持 |
| 可排序/筛选的表格 | ❌ | ✅ 需要 InteractiveTable | 需要交互逻辑 |
| 简单代码块 | ✅ 语法高亮 | ❌ | `marked` + highlight.js |
| 可运行的代码 | ❌ | ✅ 需要 CodePlayground | 需要沙箱执行 |
| 简单列表 | ✅ | ❌ | `marked` 原生支持 |
| 可拖拽排序的卡片 | ❌ | ✅ 需要 CardDeck | 需要 drag & drop |
| 静态图片 | ✅ `![alt](url)` | ❌ | `marked` 原生支持 |
| 可交互的图表 | ❌ | ✅ 需要 ChartComponent | 需要 ECharts/D3 |
| 简单数学公式 | ✅ KaTeX | ❌ | 已集成 |
| 可调参的函数图像 | ❌ | ✅ 需要 FunctionPlotter | 需要滑块+实时渲染 |
| 情绪状态展示 | ❌ | ✅ 需要 EmotionCard | 需要动态可视化 |
| 测验表单 | ❌ | ✅ 需要 QuizForm | 需要填写+提交 |
| 知识点依赖关系 | ❌ | ✅ 需要 KnowledgeGraph | 需要 DAG 可视化+交互 |

### 10.5 策略选择：严格分层 + 渐进增强

**当前策略（严格分层）**：

```
Markdown 层：处理所有"展示型"内容（表格、代码、公式、列表）
Generative 层：只处理"交互型"内容（测验、情绪、知识图谱）

原则：如果一个内容只需要"看"，放 Markdown 层；
     如果需要"点/拖/填/提交"，放 Generative 层。
```

**优点**：
- Markdown 渲染器已经覆盖了 90% 的 LLM 输出
- Generative 组件数量可控（5-8 个）
- 职责清晰，不会出现"表格到底用 Markdown 渲染还是用组件渲染"的混乱

**未来扩展（渐进增强）**：

当业务需要"超 Markdown"能力时，按需新增 Generative 组件：

```
扩展组件（按需添加）：
├── InteractiveTable  ← 当用户需要可排序表格时
├── ChartComponent    ← 当需要可交互图表时
└── CodePlayground    ← 当需要代码沙箱时

扩展方式：
1. 后端新增 Function Calling 工具定义
2. 前端新增组件注册到 Registry
3. 不影响现有组件，完全增量式
```

### 10.6 Markdown 渲染管线的增强

当前项目的 Markdown 渲染管线基于 `marked` + `KaTeX` + `Mermaid`，但默认配置只输出裸 HTML，视觉效果差。需要通过自定义 `marked.Renderer` 增强输出：

**自定义 Renderer 的核心逻辑**：

```javascript
const customRenderer = new marked.Renderer()

// 1. Emoji 标题识别：将 "📖 投资课第五课" 拆分为 emoji + 文字
customRenderer.heading = function (data) {
  const match = data.text.match(emojiSectionRegex)
  if (match) {
    return `<h${depth} class="ai-heading ai-heading--emoji">
      <span class="ai-heading-emoji">${emoji}</span>
      <span class="ai-heading-text">${title}</span>
    </h${depth}>`
  }
  return `<h${depth} class="ai-heading">${text}</h${depth}>`
}

// 2. 表格增强：包裹 wrapper + 语义化 class
customRenderer.table = function (data) {
  return `<div class="ai-table-wrapper">
    <table class="ai-table">...</table>
  </div>`
}

// 3. Emoji 引用块识别：将 > 🤔 但是... 转为 callout 卡片
customRenderer.blockquote = function (data) {
  const match = data.text.match(emojiSectionRegex)
  if (match) {
    return `<div class="ai-callout">
      <span class="ai-callout-emoji">${emoji}</span>
      <div class="ai-callout-content">${content}</div>
    </div>`
  }
  return `<blockquote class="ai-blockquote">${text}</blockquote>`
}

// 4. 列表增强：自定义圆点 + 计数器
customRenderer.list = function (data) { ... }

// 5. 代码块增强：带语言标签头
customRenderer.code = function (data) {
  return `<div class="ai-code-block">
    <div class="ai-code-header">${lang}</div>
    <pre class="ai-code-content"><code>${code}</code></pre>
  </div>`
}
```

**CSS 样式增强要点**：

| 元素 | 增强前 | 增强后 |
|------|--------|--------|
| 表格 | 1px 灰色边框，无区分 | 深色表头 + 斑马纹行 + 圆角边框 + 悬停高亮 |
| Emoji 标题 | emoji 和文字混排 | 水平排列 + 底部分隔线 |
| 列表 | 默认圆点 + 4px 间距 | 自定义彩色圆点 + 合理行高 |
| 代码块 | 裸 `<pre>` | 深色背景 + 语言标签头 + 圆角 |
| 分割线 | 1px 灰线 | 渐变淡出效果 |
| 引用块 | 左侧竖线 | Emoji callout 卡片 / 带圆角的引用块 |

### 10.7 Vue 3 vs React 在渲染管线上的对比

**核心差异**：两种方案在渲染管线的分层逻辑上是相同的——文本走 Markdown，交互走 Generative 组件。差异在于"组件在哪里执行"。

```
React 方案 (RSC + Vercel AI SDK):
  LLM tool_call → 服务端执行组件 → 流式推送渲染结果 → 客户端显示
  特点：组件在服务端执行，客户端无需预注册

Vue 3 方案 (Client Dynamic Render):
  LLM tool_call → 后端转为 UI JSON → 客户端查找本地组件 → 动态渲染
  特点：组件在客户端执行，需要预注册到 Registry
```

**关键结论**：RSC 的"服务端渲染组件"能力，解决的是"组件在哪里执行"的问题，不是"组件如何发现"的问题。无论是 React 还是 Vue，LLM 的文本输出都走 Markdown 渲染，tool_calls 才走 Generative 组件。**这个分层是架构层面的，与框架无关。**

**Vue 3 在流式场景的隐性优势**：

教学对话中，情感值、信任度是持续变化的，不是一次性设置：

```
时间线:  t0 → t1 → t2 → t3 → t4
情感值:  0.5 → 0.6 → 0.55 → 0.7 → 0.8

React: 每次 setContent → 组件 re-render → VDOM diff → 可能触发子树更新
       需要 useCallback/useMemo/React.memo 精细优化

Vue:   每次 ref 变化 → Proxy 触发 → 只更新绑定该数值的 DOM 节点
       不需要手动优化，依赖收集在首次渲染时已完成
```

Vue 的细粒度响应式在"内容持续更新"的流式场景下天然高效。

### 10.8 RSC 对 Cos2Edu 不是必需的原因

RSC 的核心价值是"服务端渲染组件，客户端无需预注册"。但 Cos2Edu 的场景中：

1. **组件数量有限**：5-8 个教学组件，全部预注册的成本极低
2. **后端是 FastAPI**：不是 Next.js，无法直接使用 RSC。要用 RSC 需要引入 Next.js 作为中间层，架构复杂度剧增
3. **交互是双向的**：QuizForm 需要客户端事件处理，RSC 的服务端组件无法直接处理交互
4. **多 slot 渲染**：sidebar/overlay/panel 需要客户端精确控制 DOM 位置，RSC 的流式推送难以处理

```
如果选择 React + RSC 方案，架构会变成：

  FastAPI (业务逻辑)
       ↕ HTTP
  Next.js (RSC 渲染层)     ← 新增一个完整的服务！
       ↕ WS
  React Client

  问题：FastAPI 和 Next.js 之间的组件状态如何同步？
  问题：谁负责 LLM 调用？FastAPI 还是 Next.js？
  问题：Tauri 打包时需要同时启动 FastAPI + Next.js？
```

**结论**：在 Cos2Edu 的约束下（有限组件 + FastAPI 后端 + 双向交互 + 多 slot），Vue 3 的"数据驱动客户端渲染"模式比 React RSC 的"服务端渲染组件"模式更简洁高效。
