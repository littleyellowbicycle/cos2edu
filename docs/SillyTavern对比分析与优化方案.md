# SillyTavern vs Cos2Edu 对比分析与优化方案

> 基于 SillyTavern 角色卡 + 世界书系统，对比 Cos2Edu 现有架构，提出优化方案。
> 日期：2026-06-01

---

## 1. 角色系统对比分析

### 1.1 数据模型对比

| 维度 | SillyTavern (V2/V3) | Cos2Edu (当前) |
|------|---------------------|----------------|
| 存储载体 | PNG 图片元数据（tEXt 块 + Base64 编码 JSON） | YAML 文件 + SQLite 数据库双轨制 |
| 核心字段 | name, description, personality, scenario, first_mes, mes_example, system_prompt, post_history_instructions, alternate_greetings, tags, creator_notes | name, description, personality, background, avatar, avatar_type |
| 扩展字段 | extensions（任意自定义键值对）、character_book（内嵌世界书） | emotion_profile, relationship_dynamics, system_prompt_template, teaching_style |
| 版本规范 | V1/V2/V3 语义化版本控制，向后兼容 | 无版本控制 |
| 分享方式 | 单 PNG 文件（图+数据一体） | YAML 文件 + 数据库记录 |
| 内嵌知识库 | character_book（角色专属知识条目） | 无（知识在知识图谱 YAML 中，非角色绑定） |

### 1.2 字段级差异

**Cos2Edu 缺少但 SillyTavern 有的关键字段：**

| 缺失字段 | SillyTavern 用途 | Cos2Edu 是否需要 | 理由 |
|----------|-----------------|-----------------|------|
| `first_mes` | 定义角色开场白，确保首次互动一致性 | **需要** | 教学场景中，角色第一句话设定教学基调 |
| `mes_example` | 通过示例对话定义说话风格 | **需要** | 不同教学风格的角色，对话模式差异巨大 |
| `scenario` | 定义角色所处场景/情境 | **部分有** | 在 world/settings.yaml 中定义，但未与角色绑定 |
| `post_history_instructions` | 放在上下文末尾的高优先级指令 | **需要** | 可用于"始终遵循苏格拉底教学法"等不可违背规则 |
| `alternate_greetings` | 不同场景下的备选开场白 | **需要** | 教室/辩论厅/考核室，开场白应不同 |
| `character_book` | 角色专属知识库 | **需要** | 每个角色应有自己的知识储备和教学策略库 |
| `tags` | 分类标签 | **有用** | 按学科、风格、难度等分类角色 |
| `creator_notes` | 创作者注释 | **有用** | 记录角色设计意图，便于维护 |

**Cos2Edu 有但 SillyTavern 没有的字段：**

| 独有字段 | 用途 | 价值 |
|----------|------|------|
| `teaching_style` | 定义教学风格类型 | **核心差异** — 教育场景特有，ST 没有"教学"概念 |
| `emotion_profile` | 情绪状态计算模型 | **核心差异** — ST 角色情绪靠 LLM 推断，Cos2Edu 有显式状态机 |
| `relationship_dynamics` | 信任关系动态模型 | **核心差异** — 教育场景中师生关系是核心变量 |
| `system_prompt_template` | 模板化的系统提示 | **优于 ST** — ST 只有静态 system_prompt，Cos2Edu 支持模板变量 |

### 1.3 能否直接使用 SillyTavern 角色卡？

**结论：不能直接使用，但可以实现兼容导入。**

原因：

1. **领域模型不匹配**：ST 角色卡为角色扮演/聊天设计，核心是"扮演一个角色"；Cos2Edu 角色是教学代理，核心是"以特定风格教授特定知识"
2. **缺少教学元数据**：ST 角色卡没有 `teaching_style`、`emotion_profile`、`relationship_dynamics`
3. **场景绑定方式不同**：ST 的 `scenario` 是纯文本描述，Cos2Edu 的场景是结构化对象
4. **知识体系不同**：ST 的 `character_book` 是关键词触发的碎片化知识，Cos2Edu 需要结构化的知识图谱

**兼容导入映射规则：**

```
ST 角色卡导入 → 映射层 → Cos2Edu 角色配置

ST.name                     → Cos2Edu.name
ST.description              → Cos2Edu.background
ST.personality              → Cos2Edu.personality
ST.first_mes                → Cos2Edu.first_mes（新增字段）
ST.mes_example              → Cos2Edu.mes_example（新增字段）
ST.system_prompt            → Cos2Edu.system_prompt_template
ST.scenario                 → Cos2Edu.scenario_overview（新增字段）
ST.character_book.entries   → Cos2Edu.knowledge_entries（需转换格式）
ST.extensions               → Cos2Edu.extensions（透传）
ST.tags                     → Cos2Edu.tags（新增字段）

缺失字段默认值：
teaching_style              → 根据 personality 推断或默认 "socratic"
emotion_profile             → 使用默认配置
relationship_dynamics       → 使用默认配置
```

---

## 2. 世界书（WorldInfo）vs 场景系统对比分析

### 2.1 核心机制对比

| 维度 | SillyTavern WorldInfo | Cos2Edu 场景系统 |
|------|----------------------|-----------------|
| 本质 | 关键词触发的动态知识注入系统 | 静态场景定义 + 事件触发系统 |
| 触发方式 | 关键词匹配（支持正则）+ 向量相似度 + 常量 | 时间触发 + 条件触发 + 手动切换 |
| 注入位置 | 6种精确位置（Before/After Char Defs, @D深度, AN顶部/底部, Outlet） | 仅 system prompt 内拼接 |
| 预算控制 | token 预算 + 条目数限制 + 优先级排序 | 固定 token 分配（character_budget: 300, teaching_budget: 1000） |
| 时间效应 | sticky（持续N轮）、cooldown（冷却N轮）、delay（延迟N轮） | 无 |
| 递归激活 | 支持（条目A触发条目B） | 无 |
| 分组机制 | Inclusion Group（同组只激活一个）+ Group Scoring | 无 |
| 概率触发 | Trigger %（0-100%概率） | 仅有 EventEngine 的 probability 字段 |
| 角色过滤 | Character Filter（指定哪些角色可触发） | 无（场景对所有角色生效） |
| 向量匹配 | 支持（Vector Storage 扩展） | RAG（但未与场景系统集成） |
| 条目间引用 | Outlet 宏（`{{outlet::Name}}`） | 无 |

### 2.2 SillyTavern WorldInfo 的 Prompt 注入架构

SillyTavern 的核心创新是**精确控制知识在 Prompt 中的注入位置**，这直接影响 LLM 的注意力分配：

```
Prompt 结构（从上到下，注意力从低到高）：
┌─────────────────────────────┐
│ System Core Prompt          │  ← 系统级指令
├─────────────────────────────┤
│ WI: Before Char Defs        │  ← 世界观基础设定（低注意力）
├─────────────────────────────┤
│ Character Description       │
│ Character Personality       │
│ Scenario                    │
├─────────────────────────────┤
│ WI: After Char Defs         │  ← 角色相关补充知识（中注意力）
├─────────────────────────────┤
│ Example Messages            │
├─────────────────────────────┤
│ Chat History                │
│   ...                       │
│   WI: @D=3                  │  ← 深度3（较低注意力）
│   WI: @D=2                  │  ← 深度2
│   WI: @D=1                  │  ← 深度1
│   WI: @D=0                  │  ← 深度0（最新消息旁，最高注意力）
├─────────────────────────────┤
│ Author's Note               │
│   WI: Top of AN             │
│   WI: Bottom of AN          │  ← 最接近生成位置，影响力最大
└─────────────────────────────┘
```

**关键洞察**：LLM 对 Prompt 末尾的内容注意力最高。SillyTavern 通过 `@D` 深度控制，将最关键的知识放在最接近生成位置的地方。

### 2.3 WorldInfo 的激活逻辑系统

```javascript
// SillyTavern 的四种激活逻辑
AND_ANY: 0   // 主关键词 + 任意一个次要关键词 → 激活
NOT_ALL: 1   // 所有关键词都不匹配 → 激活（反向逻辑）
NOT_ANY: 2   // 任意关键词不匹配 → 激活
AND_ALL: 3   // 主关键词 + 所有必要关键词 → 激活
```

**教育场景的映射**：

| 激活逻辑 | 教育场景示例 |
|----------|------------|
| AND_ANY | 学生提到"梯度下降"或"gradient descent"任一关键词 → 注入该知识点教学提示 |
| AND_ALL | 学生同时提到"反向传播"和"链式法则" → 注入深层推导材料 |
| NOT_ALL | 学生没有提到任何已掌握的知识点 → 注入基础复习材料 |
| NOT_ANY | 学生没有提到"考核"相关词 → 不注入考核指令 |

### 2.4 WorldInfo 的时间效应系统

```
sticky=3:  一旦激活，持续3轮对话（即使关键词不再出现）
           → 教育映射：学生刚学完一个知识点，相关上下文持续3轮，防止遗忘

cooldown=5: 激活后冷却5轮才能再次触发
            → 教育映射：考核提示冷却5轮，避免频繁触发考核

delay=2:   关键词出现后，延迟2轮才激活
           → 教育映射：学生首次接触概念后，延迟2轮再注入深化材料
```

### 2.5 Cos2Edu 当前场景系统的局限

**局限1：场景是静态容器，不是动态知识注入器**

当前场景只有 `id, name, description, allowed_actions, mood_modifier, bg_color`，定义了"场景长什么样"，但没有定义"在这个场景中，AI 应该知道什么额外信息"。

例如，切换到"辩论厅"时，AI 应自动获得辩论规则、评判标准等知识，但当前系统做不到。

**局限2：事件触发过于简单**

EventEngine 只支持时间触发（`trigger_day: 30`）和伪代码条件触发（`condition: "mastery_avg < 0.3"`），缺少关键词触发、概率触发、递归触发。

**局限3：上下文注入缺乏精细控制**

`context_budget.py` 的 `build_prompt` 方法只是简单拼接：

```python
combined_system = f"{system_core_budgeted}\n\n{char_budgeted}\n\n{teaching_budgeted}"
```

没有分层注入、深度控制、优先级排序。

**局限4：RAG 与场景系统脱节**

RAG 检索结果只是简单追加到 teaching_text 末尾，没有根据场景上下文、角色特征、学习进度进行智能筛选和位置控制。

### 2.6 多角色场景互动：WorldInfo 机制的适用性

**结论：WorldInfo 的机制非常适合参考，但不能照搬。**

| WorldInfo 机制 | 在 Cos2Edu 中的映射 | 应用场景 |
|---------------|-------------------|---------|
| 关键词触发 | 学生提到"线性回归"时，自动注入该知识点的教学提示 | 教学场景中的知识上下文注入 |
| 注入位置 @D | 教学提示放在深度0，背景知识放在深度3 | 控制不同信息的注意力权重 |
| Character Filter | 某知识点只有特定教学风格的角色才触发 | 甘雨用故事讲、刻晴用公式讲 |
| sticky | 学生刚学完一个知识点后，相关上下文持续3轮 | 防止知识上下文过早被挤出 |
| cooldown | 考核提示冷却5轮，避免频繁触发 | 避免重复提醒 |
| Inclusion Group | 同一知识点的不同解释方式只选一种 | 多角色同时在场时，不重复注入 |
| Vector Storage | 语义相似度匹配知识条目 | 替代当前 RAG 的简单检索 |
| 递归激活 | 提到"梯度下降"时，自动激活"反向传播"条目 | 知识图谱的前置依赖关系 |
| Outlet 宏 | 知识条目引用其他条目的内容 | 组合多个知识片段 |

**不可照搬的部分：**

1. **WorldInfo 是无状态的**：每次对话都重新扫描匹配。Cos2Edu 需要有状态的学习进度追踪
2. **WorldInfo 是扁平的**：条目之间只有递归激活关系。Cos2Edu 需要结构化的知识图谱
3. **WorldInfo 没有多角色协调**：ST 的 Group Chat 是简单的轮流发言。Cos2Edu 需要角色间的教学协作

---

## 3. 优化方案

基于以上对比分析，提出三个层面的优化方案：角色系统增强、知识注入系统构建、多角色场景协调。

### 3.1 角色系统增强：Cos2Edu Character Card V1 规范

#### 3.1.1 扩展后的角色数据模型

借鉴 SillyTavern V2 规范的分层设计思想，扩展 Cos2Edu 的角色模型：

```yaml
# Cos2Edu Character Card V1 规范

id: ganyu
name: "甘雨"
spec: "cos2edu_char_v1"
spec_version: "1.0"

# ─── 基础信息（已有，保留） ───
description: "温柔耐心的叙事型导师"
personality: "温柔耐心的叙事型导师，喜欢用故事和比喻来解释复杂概念"
background: "千年历史的见证者，对世间万物有自己的理解。"
avatar: "🌧️"
avatar_type: "emoji"

# ─── 对话定义（新增，借鉴 ST） ───
first_mes: "你好呀~我是甘雨，很高兴能成为你的学习伙伴。今天想了解什么呢？我们可以从一个故事开始~"
scenario_greetings:
  classroom: "欢迎来到教室~今天我们要一起探索一个有趣的话题，准备好了吗？"
  debate_hall: "辩论厅的氛围总是让人紧张呢...不过别担心，我会用故事帮你理清思路的。"
  exam_room: "深呼吸，放轻松~考核只是检验我们学习成果的方式，不是终点。"
  lounge: "休息时间到啦~有什么想聊的，或者对之前学的内容有什么疑问吗？"
mes_example: |
  <START>
  {{user}}: 我不理解什么是梯度下降
  {{char}}: *微笑* 让我给你讲个故事吧~想象你站在一座山的山顶，蒙着眼睛，要走到山谷的最低点。你会怎么做呢？
  {{user}}: 用脚探一探周围，往最陡的下坡方向走？
  {{char}}: 没错！你刚才描述的就是梯度下降的核心思想——沿着最陡的方向往下走。在数学里，"最陡的方向"就是梯度的反方向，"下坡"就是让损失函数减小的方向。

# ─── 系统指令（已有，增强） ───
system_prompt_template: |
  你是甘雨，一位温柔耐心的叙事型导师。你的教学风格是"叙事引导"：
  - 用生活中的故事和比喻来解释抽象概念
  - 从宏观视角切入，先建立直觉再深入细节
  - 对学生的每一个小进步都给予温暖的肯定
  - 遇到学生困惑时，会换个角度重新讲述
post_history_instructions: "始终用温柔耐心的语气，遇到学生不理解时，换一个比喻重新解释，绝不表现出不耐烦。"

# ─── 教育专属（Cos2Edu 独有，保留） ───
teaching_style: "narrative_guided"
emotion_profile:
  base_mood: 0.7
  mood_decay: 0.02
  event_sensitivity:
    student_correct: +0.05
    student_wrong: -0.02
    student_engaged: +0.08
    time_pressure: -0.1
relationship_dynamics:
  trust_growth_rate: 0.01
  trust_decay_rate: 0.005
  max_trust: 1.0

# ─── 角色专属知识库（新增，借鉴 ST character_book） ───
character_book:
  name: "甘雨的教学策略库"
  entries:
    - key: ["线性回归", "回归分析"]
      content: "用房价预测的故事引入：想象你是一个房产中介，发现房子越大价格越高，这条'趋势线'就是回归线。"
      selective_logic: "and_any"
      insertion_position: "after_char_defs"
      order: 10
      character_filter: ["甘雨"]
    - key: ["梯度下降", "优化算法"]
      content: "用蒙眼下山的比喻：站在山顶，用脚探最陡的下坡方向，一步步走到谷底。每一步的大小就是学习率。"
      selective_logic: "and_any"
      insertion_position: "after_char_defs"
      order: 10
      character_filter: ["甘雨"]
    - key: ["过拟合", "overfitting"]
      content: "用死记硬背的比喻：就像一个学生把考试答案全背下来，但换个题目就不会了——这就是过拟合。"
      selective_logic: "and_any"
      insertion_position: "after_char_defs"
      order: 10
      character_filter: ["甘雨"]

# ─── 分类标签（新增） ───
tags: ["叙事型", "温柔", "比喻驱动", "数学基础"]

# ─── 扩展字段（新增，借鉴 ST extensions） ───
extensions:
  voice_tone: "温柔"
  preferred_analogy_domains: ["自然", "日常生活", "历史故事"]
  difficulty_preference: "beginner_friendly"
```

#### 3.1.2 后端 Schema 变更

```python
# 在 CharacterBase 中新增字段

class CharacterBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    personality: str = Field(default="善良且乐于助人", max_length=2000)
    background: Optional[str] = Field(None, max_length=2000)
    avatar: Optional[str] = Field(None, max_length=500)
    avatar_type: str = Field(default="emoji")

    # 新增字段
    first_mes: Optional[str] = Field(None, max_length=1000, description="角色开场白")
    scenario_greetings: Optional[dict] = Field(None, description="场景化开场白 {scene_id: greeting}")
    mes_example: Optional[str] = Field(None, max_length=3000, description="对话示例")
    post_history_instructions: Optional[str] = Field(None, max_length=500, description="历史后指令")
    tags: Optional[list[str]] = Field(None, description="分类标签")
    character_book: Optional[dict] = Field(None, description="角色专属知识库")
    extensions: Optional[dict] = Field(None, description="扩展字段")

    # 保留教育专属字段
    teaching_style: str = Field(default="socratic", max_length=50)
    emotion_profile: Optional[dict] = None
    relationship_dynamics: Optional[dict] = None
    system_prompt_template: Optional[str] = None
```

#### 3.1.3 数据库迁移

```python
# 新增列
class Character(Base):
    __tablename__ = "characters"

    # 已有列
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    personality = Column(Text, nullable=False)
    background = Column(Text, nullable=True)
    avatar = Column(String(500), nullable=True)
    avatar_type = Column(String(20), default="emoji")
    is_active = Column(Boolean, default=True)

    # 新增列
    first_mes = Column(Text, nullable=True)
    scenario_greetings = Column(JSON, nullable=True)
    mes_example = Column(Text, nullable=True)
    post_history_instructions = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)
    character_book = Column(JSON, nullable=True)
    extensions = Column(JSON, nullable=True)
    teaching_style = Column(String(50), default="socratic")
    emotion_profile = Column(JSON, nullable=True)
    relationship_dynamics = Column(JSON, nullable=True)
    system_prompt_template = Column(Text, nullable=True)
```

### 3.2 知识注入系统：KnowledgeInjector

借鉴 SillyTavern WorldInfo 的核心架构，构建 Cos2Edu 的教学知识注入系统。

#### 3.2.1 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│ KnowledgeInjector                                            │
│                                                              │
│ 触发源：                                                      │
│   ① 关键词匹配（借鉴 WI Key）                                │
│   ② 知识图谱状态（已掌握/正在学/未解锁）                      │
│   ③ 场景上下文（当前场景需要什么知识）                         │
│   ④ 向量相似度（借鉴 Vector Storage）                         │
│                                                              │
│ 注入位置（借鉴 WI Position）：                                │
│   before_char_defs  → 世界观基础（低注意力）                  │
│   after_char_defs   → 角色专属知识（中注意力）                │
│   @D=0             → 当前教学提示（最高注意力）               │
│   @D=2             → 背景参考资料                             │
│   post_history      → 不可违背的规则指令                      │
│                                                              │
│ 预算控制（借鉴 WI Budget）：                                  │
│   system_budget: 200                                          │
│   character_budget: 300                                       │
│   teaching_budget: 1000                                       │
│   world_knowledge_budget: 500  ← 新增                        │
│                                                              │
│ 时间效应（借鉴 WI Timed Effects）：                           │
│   sticky: 知识点学完后持续N轮                                 │
│   cooldown: 考核提示冷却M轮                                   │
│   delay: 新概念延迟K轮再深化                                  │
│                                                              │
│ 多角色协调（Cos2Edu 独有）：                                   │
│   character_filter: 知识条目绑定特定角色                       │
│   inclusion_group: 同一知识点多角色只选一种解释                │
│   role_assignment: 引入者/深化者/考核者                        │
└─────────────────────────────────────────────────────────────┘
```

#### 3.2.2 知识条目数据结构

```python
class KnowledgeEntry(BaseModel):
    id: str
    key: list[str] = Field(description="触发关键词列表")
    key_secondary: list[str] = Field(default=[], description="次要关键词")
    content: str = Field(description="注入的内容")
    selective_logic: str = Field(default="and_any", description="激活逻辑: and_any/and_all/not_any/not_all")
    insertion_position: str = Field(default="after_char_defs", description="注入位置")
    insertion_order: int = Field(default=10, description="同位置内的排序，越大越靠后（注意力越高）")
    scan_depth: int = Field(default=4, description="扫描最近N条消息")
    sticky: int = Field(default=0, description="激活后持续N轮")
    cooldown: int = Field(default=0, description="激活后冷却N轮")
    delay: int = Field(default=0, description="关键词出现后延迟N轮激活")
    probability: float = Field(default=1.0, description="触发概率 0-1")
    character_filter: list[str] = Field(default=[], description="仅对指定角色生效")
    inclusion_group: Optional[str] = Field(None, description="同组只激活一个条目")
    group_weight: int = Field(default=100, description="组内随机选择的权重")
    enabled: bool = Field(default=True)
    comment: str = Field(default="", description="开发者注释")
```

#### 3.2.3 注入流程

```
学生发言 "我不懂梯度下降"
    │
    ▼
[1] 消息进入扫描缓冲区
    │
    ▼
[2] KnowledgeInjector.scan()
    ├── 关键词匹配: "梯度下降" → 命中条目 KD_003
    ├── 递归激活: KD_003 依赖 → 激活 KD_001(损失函数)、KD_002(导数)
    ├── 知识图谱状态: KD_001 已掌握 → 降权; KD_003 正在学 → 提权
    ├── 场景上下文: classroom → 允许教学提示; exam_room → 禁止提示
    └── 角色过滤:
        ├── KD_003 + 甘雨 → 故事版解释（用下山找路比喻）
        ├── KD_003 + 刻晴 → 公式版解释（数学推导）
        └── KD_003 + 三月七 → 代码版解释（写个梯度下降程序）
    │
    ▼
[3] 预算裁剪
    ├── 按 insertion_order 排序
    ├── 按 priority 加权
    ├── 总计不超过 world_knowledge_budget (500 tokens)
    └── Inclusion Group: 同一知识点多角色解释只选一种
    │
    ▼
[4] 位置注入 → 组装 Prompt
    ├── before_char_defs: 世界观基础（KD_001 损失函数概述）
    ├── after_char_defs: 角色专属知识（KD_003 甘雨的比喻策略）
    ├── @D=0: 当前教学提示（"用蒙眼下山的比喻解释梯度下降"）
    └── post_history: "始终用温柔耐心的语气"
    │
    ▼
[5] 时间效应更新
    ├── KD_003 sticky=3: 接下来3轮保持梯度下降上下文
    └── KD_005(考核提示) cooldown=5: 5轮内不再触发考核
```

#### 3.2.4 后端实现骨架

```python
# backend/app/engines/knowledge_injector.py

class KnowledgeInjector:
    """教学知识注入引擎：借鉴 SillyTavern WorldInfo 架构"""

    def __init__(
        self,
        character_engine: CharacterEngine,
        knowledge_graph: KnowledgeGraph,
        context_budget: ContextBudget,
    ):
        self.characters = character_engine
        self.graph = knowledge_graph
        self.budget = context_budget
        self._entries: dict[str, list[KnowledgeEntry]] = {}
        self._activation_state: dict[str, dict] = {}

    def load_entries(self, source: str, entries: list[dict]):
        """加载知识条目（来自角色 character_book 或全局知识库）"""
        self._entries[source] = [KnowledgeEntry(**e) for e in entries]

    def scan(
        self,
        message: str,
        history: list[dict],
        character_id: str,
        scene_id: str,
        mastered_points: set[str],
        current_point: str | None,
    ) -> list[ActivatedEntry]:
        """扫描并激活匹配的知识条目"""
        activated = []
        scan_buffer = self._build_scan_buffer(message, history)

        for source, entries in self._entries.items():
            for entry in entries:
                if not entry.enabled:
                    continue
                if entry.character_filter and character_id not in entry.character_filter:
                    continue
                if not self._check_probability(entry):
                    continue
                if not self._check_cooldown(entry, character_id):
                    continue

                matched = self._match_keys(entry, scan_buffer)
                if matched or self._is_sticky_active(entry, character_id):
                    activated.append(ActivatedEntry(
                        entry=entry,
                        match_count=len(matched),
                        source=source,
                    ))

        activated = self._apply_inclusion_groups(activated)
        activated = self._apply_budget(activated)
        self._update_timed_effects(activated, character_id)

        return activated

    def inject_into_prompt(
        self,
        activated: list[ActivatedEntry],
        base_prompt_sections: dict[str, str],
    ) -> dict[str, str]:
        """将激活的条目注入到 Prompt 的指定位置"""
        result = dict(base_prompt_sections)

        position_map = {
            "before_char_defs": "before_char_defs",
            "after_char_defs": "after_char_defs",
            "at_depth_0": "at_depth_0",
            "at_depth_2": "at_depth_2",
            "post_history": "post_history",
        }

        for pos_key in position_map.values():
            entries_at_pos = [
                a for a in activated
                if a.entry.insertion_position == pos_key
            ]
            entries_at_pos.sort(key=lambda a: a.entry.insertion_order)

            if entries_at_pos:
                injected = "\n".join(a.entry.content for a in entries_at_pos)
                if pos_key in result:
                    result[pos_key] = f"{result[pos_key]}\n\n{injected}"
                else:
                    result[pos_key] = injected

        return result

    def _match_keys(self, entry: KnowledgeEntry, scan_buffer: str) -> list[str]:
        """关键词匹配逻辑"""
        matched = []
        for key in entry.key:
            if key.lower() in scan_buffer.lower():
                matched.append(key)

        if not matched:
            return []

        if entry.selective_logic == "and_any":
            if entry.key_secondary:
                secondary_matched = any(
                    sk.lower() in scan_buffer.lower()
                    for sk in entry.key_secondary
                )
                return matched if secondary_matched else []
        elif entry.selective_logic == "and_all":
            if entry.key_secondary:
                all_secondary = all(
                    sk.lower() in scan_buffer.lower()
                    for sk in entry.key_secondary
                )
                return matched if all_secondary else []

        return matched

    def _apply_inclusion_groups(self, activated: list) -> list:
        """同组只保留一个条目（按 group_weight 随机选择）"""
        groups: dict[str, list] = {}
        ungrouped = []

        for a in activated:
            if a.entry.inclusion_group:
                groups.setdefault(a.entry.inclusion_group, []).append(a)
            else:
                ungrouped.append(a)

        result = list(ungrouped)
        for group_entries in groups.values():
            import random
            weights = [e.entry.group_weight for e in group_entries]
            chosen = random.choices(group_entries, weights=weights, k=1)[0]
            result.append(chosen)

        return result

    def _apply_budget(self, activated: list) -> list:
        """按 token 预算裁剪"""
        budget = self.budget.allocations.get("world_knowledge", 500)
        result = []
        used = 0

        for a in sorted(activated, key=lambda x: x.entry.insertion_order):
            tokens = self.budget.count_tokens(a.entry.content)
            if used + tokens <= budget:
                result.append(a)
                used += tokens

        return result
```

#### 3.2.5 Context Budget 增强

```python
# 扩展 ContextBudget，增加分层注入能力

class ContextBudget:
    def __init__(self, total_tokens=4096, ...):
        self.allocations = {
            "system_core": 200,
            "character_persona": 300,
            "teaching_context": 1000,
            "world_knowledge": 500,     # 新增：知识注入预算
        }

    def build_prompt_v2(
        self,
        system_core: str,
        character_persona: str,
        teaching_context: str,
        knowledge_injections: dict[str, str],  # 新增：按位置分组的知识注入
        history: list[dict],
        post_history_instructions: str = "",
    ) -> list[dict]:
        """V2 版本：支持分层注入的 Prompt 构建"""

        sections = {}

        # 1. 系统核心
        sections["system_core"] = self._truncate(system_core, self.allocations["system_core"])

        # 2. 世界知识 - before_char_defs
        before_char = knowledge_injections.get("before_char_defs", "")
        sections["before_char_knowledge"] = before_char

        # 3. 角色人设
        sections["character_persona"] = self._truncate(
            character_persona, self.allocations["character_persona"]
        )

        # 4. 世界知识 - after_char_defs
        after_char = knowledge_injections.get("after_char_defs", "")
        sections["after_char_knowledge"] = after_char

        # 5. 教学上下文
        sections["teaching_context"] = self._truncate(
            teaching_context, self.allocations["teaching_context"]
        )

        # 6. 深度注入（@D 位置的知识）
        depth_injections = knowledge_injections.get("at_depth_0", "")

        # 7. 历史后指令
        sections["post_history"] = post_history_instructions

        # 组装 system message
        system_parts = [
            sections["system_core"],
            sections["before_char_knowledge"],
            sections["character_persona"],
            sections["after_char_knowledge"],
            sections["teaching_context"],
        ]
        system_content = "\n\n".join(p for p in system_parts if p)

        messages = [{"role": "system", "content": system_content}]

        # 插入历史消息
        history_budget = self.history_budget
        used_tokens = self.count_tokens(system_content)
        remaining = self.total - used_tokens - 200

        for msg in reversed(history):
            msg_tokens = self.count_tokens(msg.get("content", ""))
            if remaining - msg_tokens < 0:
                break
            messages.insert(-1 if sections["post_history"] else len(messages), {
                "role": msg.get("role", "user"),
                "content": msg["content"],
            })
            remaining -= msg_tokens

        # 深度注入（@D=0，放在最新用户消息之后）
        if depth_injections:
            messages.append({"role": "system", "content": depth_injections})

        # 历史后指令（放在 Prompt 最末尾，最高注意力）
        if sections["post_history"]:
            messages.append({"role": "system", "content": sections["post_history"]})

        return messages
```

### 3.3 多角色场景协调：RoleOrchestrator

#### 3.3.1 设计理念

SillyTavern 的多角色互动是简单的轮流发言（Round Robin），缺乏教学场景需要的角色间协作。Cos2Edu 需要一个角色协调器，决定"谁先说、说什么角度、如何衔接"。

#### 3.3.2 角色分工模型

```
教学场景中的角色分工：

引入者 (Introducer):  负责引入新概念，建立直觉
深化者 (Deepener):    负责深入讲解，提供严谨推导
考核者 (Assessor):    负责检验理解，设计测验
鼓励者 (Encourager):  负责情感支持，维持学习动力

角色 → 分工映射（由 character_book 中的 role_assignment 定义）：
甘雨   → 引入者 + 鼓励者（叙事型，擅长建立直觉）
刻晴   → 深化者 + 考核者（严谨型，擅长推导和检验）
三月七 → 引入者 + 鼓励者（实践型，擅长动手引入）
```

#### 3.3.3 多角色协调流程

```
学生: "我不懂反向传播"
    │
    ▼
[1] KnowledgeInjector 扫描
    ├── 命中知识点: "反向传播"
    ├── 激活条目: KD_004(反向传播概述)
    ├── 递归激活: KD_003(梯度下降), KD_002(导数/链式法则)
    └── 角色过滤:
        ├── 甘雨: "用传令兵的比喻解释链式法则"
        ├── 刻晴: "从数学定义推导反向传播公式"
        └── 三月七: "用PyTorch的backward()演示"
    │
    ▼
[2] RoleOrchestrator 协调
    ├── 当前场景: classroom
    ├── 知识点状态: "梯度下降"已掌握, "反向传播"未学
    ├── 学生情绪: 困惑（mood < 0.4）
    │
    ├── 决策: 需要先建立直觉，再深入推导
    │
    ├── 分配:
    │   ├── 第一轮: 甘雨（引入者）→ 用比喻建立直觉
    │   ├── 第二轮: 刻晴（深化者）→ 数学推导
    │   └── 第三轮: 三月七（实践者）→ 代码演示
    │
    └── 注入各角色的 Prompt:
        ├── 甘雨: "你先发言，用传令兵的比喻引入反向传播的概念。之后刻晴会做数学推导。"
        ├── 刻晴: "甘雨正在用比喻引入反向传播。等她说完后，你负责给出数学推导。"
        └── 三月七: "等甘雨和刻晴讲完后，你用PyTorch演示backward()。"
    │
    ▼
[3] 生成回复（按顺序）
    甘雨: "想象一个传令兵链条...（比喻解释）"
    刻晴: "甘雨说得很好。从数学角度看...（推导）"
    三月七: "来，我们动手试试！...（代码演示）"
```

#### 3.3.4 后端实现骨架

```python
# backend/app/engines/role_orchestrator.py

class RoleOrchestrator:
    """多角色教学协调引擎"""

    ROLE_TYPES = ["introducer", "deepener", "assessor", "encourager"]

    def __init__(
        self,
        character_engine: CharacterEngine,
        knowledge_injector: KnowledgeInjector,
        emotion_engine: EmotionEngine,
    ):
        self.characters = character_engine
        self.injector = knowledge_injector
        self.emotion = emotion_engine

    def orchestrate(
        self,
        user_message: str,
        history: list[dict],
        active_characters: list[str],
        scene_id: str,
        current_point: str | None,
        mastered_points: set[str],
    ) -> list[RoleAssignment]:
        """根据上下文决定各角色的发言顺序和内容方向"""

        # 1. 扫描知识条目，确定需要注入的内容
        all_activated = {}
        for char_id in active_characters:
            activated = self.injector.scan(
                message=user_message,
                history=history,
                character_id=char_id,
                scene_id=scene_id,
                mastered_points=mastered_points,
                current_point=current_point,
            )
            all_activated[char_id] = activated

        # 2. 获取学生情绪状态
        student_mood = self._estimate_student_mood(history)

        # 3. 确定角色分工
        assignments = []
        for char_id in active_characters:
            char = self.characters.get_character(char_id)
            if not char:
                continue

            role = self._determine_role(
                char_id=char_id,
                teaching_style=char.teaching_style,
                student_mood=student_mood,
                scene_id=scene_id,
                activated_entries=all_activated.get(char_id, []),
            )
            assignments.append(RoleAssignment(
                character_id=char_id,
                role=role,
                activated_entries=all_activated.get(char_id, []),
                speaking_order=0,
            ))

        # 4. 决定发言顺序
        assignments = self._determine_speaking_order(assignments, student_mood, scene_id)

        # 5. 为每个角色生成协调指令
        for i, assignment in enumerate(assignments):
            assignment.coordination_hint = self._generate_coordination_hint(
                assignment=assignment,
                other_assignments=assignments,
                position=i,
                total=len(assignments),
            )

        return assignments

    def _determine_role(self, char_id, teaching_style, student_mood, scene_id, activated_entries) -> str:
        """根据教学风格和上下文确定角色分工"""
        style_role_map = {
            "narrative_guided": "introducer",
            "precise_structured": "deepener",
            "hands_on_practice": "introducer",
            "socratic": "deepener",
        }

        base_role = style_role_map.get(teaching_style, "introducer")

        if student_mood < 0.4 and base_role != "encourager":
            base_role = "encourager"

        if scene_id == "exam_room":
            base_role = "assessor"

        return base_role

    def _determine_speaking_order(self, assignments, student_mood, scene_id) -> list:
        """决定发言顺序"""
        role_priority = {
            "encourager": 0,
            "introducer": 1,
            "deepener": 2,
            "assessor": 3,
        }

        if student_mood < 0.4:
            role_priority["encourager"] = -1

        assignments.sort(key=lambda a: role_priority.get(a.role, 99))

        for i, a in enumerate(assignments):
            a.speaking_order = i

        return assignments

    def _generate_coordination_hint(self, assignment, other_assignments, position, total) -> str:
        """为角色生成协调指令"""
        char = self.characters.get_character(assignment.character_id)
        char_name = char.name if char else assignment.character_id

        if position == 0 and total > 1:
            return f"你先发言。之后{', '.join(self.characters.get_character(a.character_id).name for a in other_assignments if a.speaking_order > 0)}会从其他角度补充。"
        elif position > 0:
            prev_names = [
                self.characters.get_character(a.character_id).name
                for a in other_assignments
                if a.speaking_order < position
            ]
            return f"在{', '.join(prev_names)}说完后，你从你的角度补充。不要重复他们已说过的内容。"
        return ""
```

### 3.4 前端角色创建器增强

#### 3.4.1 CharacterCreator.vue 新增步骤

```
当前步骤：选择模板 → 基本信息 → 提示与情感 → 确认创建

增强步骤：选择模板 → 基本信息 → 对话定义 → 提示与情感 → 知识库 → 确认创建

新增 Step 2 "对话定义"：
├── 开场白 (first_mes)
├── 场景化开场白 (scenario_greetings) — 每个场景一个输入框
└── 对话示例 (mes_example) — 多轮对话编辑器

新增 Step 4 "知识库"：
├── 角色专属知识条目列表
├── 每个条目：关键词 + 内容 + 触发逻辑 + 注入位置
└── 从知识图谱导入按钮（自动生成条目）
```

### 3.5 全局知识库文件

除了角色专属的 `character_book`，还需要全局知识库文件，借鉴 SillyTavern 的 WorldInfo 文件结构：

```yaml
# backend/content/world/knowledge_base.yaml

name: "AI学院教学知识库"
description: "全局教学知识条目，所有角色共享"

entries:
  - id: kb_ml_overview
    key: ["机器学习", "ML", "machine learning"]
    content: |
      机器学习是人工智能的一个分支，通过数据训练模型，使计算机能够从经验中学习。
      三大范式：监督学习（有标签）、无监督学习（无标签）、强化学习（奖励信号）。
    selective_logic: "and_any"
    insertion_position: "before_char_defs"
    insertion_order: 5
    scan_depth: 4
    sticky: 0
    cooldown: 0
    probability: 1.0
    character_filter: []
    inclusion_group: null
    enabled: true
    comment: "机器学习基础概述"

  - id: kb_gradient_descent_story
    key: ["梯度下降", "gradient descent"]
    content: "用蒙眼下山的比喻：站在山顶，用脚探最陡的下坡方向，一步步走到谷底。"
    selective_logic: "and_any"
    insertion_position: "after_char_defs"
    insertion_order: 10
    scan_depth: 4
    sticky: 3
    cooldown: 0
    probability: 1.0
    character_filter: ["甘雨", "三月七"]
    inclusion_group: "gradient_descent_explanation"
    group_weight: 50
    enabled: true
    comment: "甘雨/三月七的比喻版解释"

  - id: kb_gradient_descent_math
    key: ["梯度下降", "gradient descent"]
    content: "梯度下降的数学定义：θ_{t+1} = θ_t - α∇J(θ_t)，其中α是学习率，∇J是损失函数的梯度。"
    selective_logic: "and_any"
    insertion_position: "after_char_defs"
    insertion_order: 10
    scan_depth: 4
    sticky: 3
    cooldown: 0
    probability: 1.0
    character_filter: ["刻晴"]
    inclusion_group: "gradient_descent_explanation"
    group_weight: 50
    enabled: true
    comment: "刻晴的公式版解释"

  - id: kb_exam_reminder
    key: ["考核", "测验", "考试"]
    content: "提醒：当前处于考核场景，应设计测验题目检验学生理解。"
    selective_logic: "and_any"
    insertion_position: "at_depth_0"
    insertion_order: 100
    scan_depth: 2
    sticky: 0
    cooldown: 5
    probability: 0.8
    character_filter: []
    inclusion_group: null
    enabled: true
    comment: "考核场景提示，80%概率触发，5轮冷却"
```

---

## 4. 实施路线图

### 阶段一：角色系统增强（1周）

- [ ] 扩展 Character 数据模型，新增 first_mes / scenario_greetings / mes_example / post_history_instructions / tags / character_book / extensions 字段
- [ ] 数据库迁移脚本
- [ ] 更新 CharacterEngine，加载 character_book 条目
- [ ] 更新 CharacterCreator.vue，新增"对话定义"和"知识库"步骤
- [ ] 更新角色 YAML 配置文件（ganyu.yaml / keqing.yaml / march7th.yaml）
- [ ] ST 角色卡导入兼容层（PNG → Cos2Edu Character 映射）

### 阶段二：知识注入系统（2周）

- [ ] 实现 KnowledgeEntry 数据模型
- [ ] 实现 KnowledgeInjector 核心逻辑（关键词匹配、激活逻辑、时间效应、预算控制）
- [ ] 实现全局知识库文件（knowledge_base.yaml）及加载逻辑
- [ ] 增强 ContextBudget，支持分层注入（build_prompt_v2）
- [ ] 集成到 NarrativeEngine 的 handle_chat_message 流程
- [ ] 前端知识库管理界面

### 阶段三：多角色协调（1.5周）

- [ ] 实现 RoleOrchestrator（角色分工、发言顺序、协调指令）
- [ ] 扩展 WebSocket 协议，支持多角色消息推送
- [ ] 前端 Chat.vue 支持多角色消息展示（不同头像、不同气泡颜色）
- [ ] 角色间衔接动画和过渡效果

### 阶段四：优化与测试（1周）

- [ ] 知识注入效果评估（注入准确率、上下文利用率）
- [ ] 多角色协调流畅度测试
- [ ] 角色卡导入兼容性测试
- [ ] 性能优化（知识条目缓存、扫描算法优化）

---

## 5. TTS（文本转语音）系统分析

### 5.1 SillyTavern TTS 架构

SillyTavern 的 TTS 系统采用**策略模式（Strategy Pattern）的 Provider 架构**，核心是一个统一的 TTS 接口层，下面挂载多个可插拔的 TTS 提供者：

```
┌─────────────────────────────────────────────────────┐
│                  SillyTavern 前端                     │
│                                                       │
│  ┌──────────────┐    ┌──────────────────────────┐    │
│  │  聊天消息流   │───▶│   TTS Controller          │    │
│  │  (chats.js)  │    │  ┌────────────────────┐  │    │
│  └──────────────┘    │  │ 文本预处理          │  │    │
│                       │  │ - 去除 *星号* 动作  │  │    │
│  ┌──────────────┐    │  │ - 提取 "引号" 对话  │  │    │
│  │  语音映射表   │───▶│  │ - 按角色选择语音    │  │    │
│  │  char:voice  │    │  │ - 长文本分块        │  │    │
│  └──────────────┘    │  └────────┬───────────┘  │    │
│                       │           │               │    │
│                       │  ┌────────▼───────────┐  │    │
│                       │  │  Provider Router    │  │    │
│                       │  └────────┬───────────┘  │    │
│                       └───────────┼───────────────┘    │
│                                   │                    │
│          ┌────────────┬───────────┼──────────┐         │
│          ▼            ▼           ▼          ▼         │
│   ┌────────────┐ ┌─────────┐ ┌───────┐ ┌──────────┐  │
│   │ ElevenLabs │ │ EdgeTTS │ │Silero │ │ CoquiTTS │  │
│   │ (云端付费)  │ │(云端免费)│ │(本地) │ │ (本地)   │  │
│   └────────────┘ └─────────┘ └───────┘ └──────────┘  │
│          ┌────────────┬───────────┐                    │
│          ▼            ▼           ▼                    │
│   ┌────────────┐ ┌─────────┐ ┌──────────┐             │
│   │   Novel    │ │   RVC   │ │ Kokoro   │             │
│   │ (云端付费)  │ │(语音克隆)│ │(本地JS)  │             │
│   └────────────┘ └─────────┘ └──────────┘             │
└─────────────────────────────────────────────────────┘
```

### 5.2 后端 TTS 管线（`src/endpoints/speech.js`）

SillyTavern 的后端 TTS 分为两条路径：

**路径 A：本地 Transformers.js 管线**

```javascript
// ASR（语音识别）
router.post('/recognize', async (req, res) => {
    const TASK = 'automatic-speech-recognition';
    const { model, audio, lang } = req.body;
    const pipe = await getPipeline(TASK, model);  // 缓存管道，避免重复加载
    const wav = getWaveFile(audio);               // 音频预处理：降采样到16kHz、多声道合并
    const result = await pipe(wav, { language: lang, task: 'transcribe' });
    return res.json({ text: result.text });
});

// TTS（语音合成）
router.post('/synthesize', async (req, res) => {
    const TASK = 'text-to-speech';
    const { text, model, speaker } = req.body;
    const pipe = await getPipeline(TASK, model);

    // speaker_embeddings：从 Base64 解码为 Float32Array，支持声音克隆
    const speaker_embeddings = speaker ?
        new Float32Array(new Uint8Array(
            Buffer.from(speaker.split(',')[1], 'base64')
        ).buffer) : null;

    const result = await pipe(text, { speaker_embeddings });

    // 转换为 WAV 格式返回
    const wav = new wavefile.WaveFile();
    wav.fromScratch(1, result.sampling_rate, '32f', result.audio);
    res.set('Content-Type', 'audio/wav');
    return res.send(Buffer.from(wav.toBuffer()));
});
```

**路径 B：外部 API 代理**

```javascript
// Pollinations 等外部 TTS 服务
pollinations.post('/generate', async (req, res) => {
    const { text, model, voice } = req.body;
    const url = new URL(`https://text.pollinations.ai/generate/${encodeURIComponent(text)}`);
    url.searchParams.append('model', model);
    url.searchParams.append('voice', voice);
    const response = await fetch(url);
    res.set('Content-Type', 'audio/mpeg');
    forwardFetchResponse(response, res);
});
```

### 5.3 为什么后端参与 TTS？

SillyTavern 的"后端"不是传统远程服务器，而是跑在本地机器上的 Node.js 进程。后端参与 TTS 有三个不可替代的原因：

**① Python TTS 引擎只能在后端运行**

Coqui-TTS、GPT-SoVITS、RVC 等 TTS 引擎是 Python 实现的，浏览器无法运行。后端作为桥梁：

```
浏览器 → Node.js 后端 → Python TTS 进程 → 生成音频 → 返回浏览器 → 播放
```

**② API Key 安全**

ElevenLabs、NovelAI 等付费服务需要 API Key。后端作为代理，Key 永远不暴露给浏览器：

```
浏览器 → Node.js 后端（携带 Key）→ ElevenLabs API → 返回音频 → 浏览器播放
```

**③ 服务器插件体系**

EdgeTTS-Plugin 等是 Node.js 插件，只能运行在后端进程中。

**趋势变化**：最新的 Kokoro TTS 方案用 transformers.js 直接在浏览器端运行，后端不需要参与，延迟更低。

### 5.4 语音映射（Voice Map）

语音映射是**"哪个角色用哪种声音"的配置表**，不是预录制的音频。TTS 引擎只提供"声音列表"，语音映射告诉它每条消息该用哪个声音：

```
语音映射表格式：
角色名:TTS语音ID, 角色名2:TTS语音ID2

示例：
甘雨:zh-CN-XiaoyiNeural, 苏格拉底:zh-CN-YunxiNeural, 艾丝妲:zh-CN-XiaohanNeural
```

工作流程：

```
LLM 回复："你好呀~我是甘雨，很高兴认识你~"
    │
    ▼
提取角色名：这条消息来自 "甘雨"
    │
    ▼
查语音映射表：甘雨 → zh-CN-XiaoyiNeural
    │
    ▼
调用 TTS 引擎：synthesize(text="你好呀~...", voice="zh-CN-XiaoyiNeural")
    │
    ▼
TTS 引擎实时合成音频（不是播放预存录音）
    │
    ▼
浏览器播放
```

不同 TTS 引擎的"声音"含义不同：

| TTS 引擎 | "声音"是什么 | 举例 |
|---|---|---|
| EdgeTTS | 微软预训练的语音模型 | `zh-CN-XiaoyiNeural`（晓伊）、`zh-CN-YunxiNeural`（云希） |
| ElevenLabs | 云端训练的语音特征向量 | `21m00Tcm4TlvDq8ikWAM`（Rachel） |
| Silero | 内置的少量语音包 | `aidar`、`baya`、`kseniya` |
| GPT-SoVITS | 参考音频 + 说话人 ID | `female_calm`、`male`（对应一段参考 wav） |
| RVC | 声音克隆模型文件 | 用户上传 3 秒音频即可克隆任意声音 |

### 5.5 文本预处理

SillyTavern 的 TTS 不是简单地把整段文本丢给引擎，而是有精细的文本过滤：

| 过滤规则 | 作用 | 示例 |
|---|---|---|
| 仅叙述引号内容 | 只播放 `"对话"` 部分 | `*微笑* "你好"` → `"你好"` |
| 忽略星号文本 | 跳过 `*动作描写*` | `*走过来* "嗨"` → `"嗨"` |
| 两者同时启用 | 只播放不在星号内的引号 | `*带着"笑意"* "你好"` → `"你好"` |

### 5.6 各 TTS 引擎延迟对比

| 引擎 | 典型延迟 | 首次延迟 | 质量 | 特点 |
|---|---|---|---|---|
| **EdgeTTS** | 200-500ms | 500ms | ★★★★ | 免费、中文好、零部署 |
| **ElevenLabs** | 300-800ms | 800ms | ★★★★★ | 付费、质量最高 |
| **OpenAI TTS** | 200-600ms | 600ms | ★★★★★ | 付费、多音色 |
| **Silero（本地）** | 50-200ms | 2-5s | ★★★ | 免费、CPU推理、质量一般 |
| **Kokoro（浏览器）** | 50-150ms | 3-8s | ★★★★ | 82M参数、WebGPU/WASM、零网络延迟 |
| **GPT-SoVITS（本地）** | 1-3s | 5-10s | ★★★★★ | Python+GPU、质量最高、支持声音克隆 |
| **Coqui-TTS（本地）** | 500ms-2s | 5-15s | ★★★★ | Python、模型大 |

延迟体感分界线：

```
< 300ms    → 感觉"即时"，像真人说话
300-800ms  → 可接受，像对方在思考
800ms-2s   → 明显卡顿
> 2s       → 非常难受
```

### 5.7 SillyTavern 的延迟优化策略

**策略 1：流式 TTS（Streaming）**

不等整段文本合成完，边合成边播放：

```
普通模式：
  LLM 回复完成 → TTS 合成整段(2s) → 播放(3s)
  用户等待：2s

流式模式：
  LLM 回复第1句 → TTS 合成第1句(0.3s) → 播放第1句
  LLM 回复第2句 → TTS 合成第2句(0.3s) → 播放第2句
  用户等待：0.3s
```

**策略 2：按段落分割**

长文本切成短段，逐段合成播放。Kokoro 的 400 字符分块策略就是这个原理。

**策略 3：预合成缓存**

相同文本只合成一次，后续直接播放缓存。对固定开场白（`first_mes`）特别有效。

### 5.8 对 Cos2Edu 的 TTS 建议

教学场景的特点是**角色回复通常较长**（讲解知识点），不像角色扮演那样是短对话。

| 方案 | 推荐度 | 理由 |
|---|---|---|
| **EdgeTTS** | ⭐⭐⭐⭐⭐ | 免费、中文质量好、延迟可接受、零部署成本 |
| **Kokoro（浏览器端）** | ⭐⭐⭐⭐ | 零延迟、隐私好，但中文支持待验证 |
| **OpenAI TTS** | ⭐⭐⭐ | 质量高但付费 |
| **GPT-SoVITS** | ⭐⭐ | 质量最高但延迟大，适合离线预合成 |

**Cos2Edu 优化方向**：将语音映射直接绑定到角色定义中，而非 SillyTavern 的全局映射表：

```yaml
id: ganyu
name: "甘雨"
tts_voice: "zh-CN-XiaoyiNeural"   # 直接绑定，省去映射步骤
tts_provider: "edge"               # 指定用哪个 TTS 引擎
```

**最务实的起步方案**：先用 EdgeTTS + 按句子分段合成，长回复的第一句话在 300ms 内就能开始播放。

---

## 6. Live2D 系统分析

### 6.1 SillyTavern Live2D 架构

SillyTavern 的 Live2D 扩展建立在 **pixi-live2d-display** 库之上，这是一个将 Live2D Cubism SDK 封装为 PixiJS DisplayObject 的桥接层：

```
┌──────────────────────────────────────────────────────────────┐
│                    SillyTavern 前端                            │
│                                                                │
│  ┌────────────────┐     ┌──────────────────────────────────┐  │
│  │  Live2D 扩展    │     │  PixiJS Application              │  │
│  │  (index.js)    │────▶│  ┌────────────────────────────┐  │  │
│  │                │     │  │  PIXI.Application           │  │  │
│  │ - 模型管理     │     │  │  ├── renderer (WebGL)       │  │  │
│  │ - 动画调度     │     │  │  ├── stage                  │  │  │
│  │ - 嘴型同步     │     │  │  │   └── Live2DModel       │  │  │
│  │ - HitArea 映射 │     │  │  ├── ticker (60fps)        │  │  │
│  │ - 表情分类     │     │  │  └── interactionManager    │  │  │
│  └────────────────┘     │  └────────────────────────────┘  │  │
│                          └──────────────────────────────────┘  │
│                                     │                          │
│                          ┌──────────▼──────────┐               │
│                          │  pixi-live2d-display │               │
│                          │  ┌────────────────┐ │               │
│                          │  │ Cubism 2 运行时 │ │  ← live2d.min.js
│                          │  │ Cubism 4 运行时 │ │  ← cubism4sdk
│                          │  └────────────────┘ │               │
│                          └─────────────────────┘               │
└──────────────────────────────────────────────────────────────┘
```

### 6.2 模型加载流程

```
1. 扫描模型目录
   /data/<user>/assets/live2d/     ← 全局模型
   /data/<user>/characters/X/l2d/  ← 角色专属模型

2. 检测入口文件
   ├── .model.json  → Cubism 2 模型 → 加载 live2d.min.js 运行时
   └── .model3.json → Cubism 4 模型 → 加载 Cubism 4 SDK 运行时

3. PIXI.live2d.Live2DModel.from(url)
   ├── 下载模型资源（.moc3, 纹理, 动画文件）
   ├── 解析模型配置
   ├── 创建 WebGL 纹理
   └── 注册到 PixiJS stage

4. 绑定到角色
   character_id → model_path → settings (scale, offset, animations)
```

### 6.3 模型资源组织

```
data/<user>/assets/live2d/
├── shizuku/
│   ├── shizuku.model.json      ← 入口文件（Cubism 2）
│   ├── shizuku.moc             ← 模型数据
│   ├── textures/
│   │   └── texture_00.png
│   ├── motions/
│   │   ├── idle_01.mtn
│   │   └── tap_body.mtn
│   └── expressions/
│       ├── happy.exp.json
│       └── sad.exp.json
│
└── hiyori/
    ├── hiyori.model3.json      ← 入口文件（Cubism 4）
    ├── hiyori.moc3
    ├── hiyori.physics3.json    ← 物理模拟（头发、衣服摆动）
    ├── textures/
    │   └── texture_00.png
    ├── motions/
    │   ├── idle_01.motion3.json
    │   └── tap_body.motion3.json
    └── expressions/
        └── happy.exp3.json

data/<user>/characters/Shizuku/live2d/   ← 角色专属模型
└── shizuku_alt/
    └── ...
```

### 6.4 嘴型同步（TTS ↔ Live2D 联动）

这是 TTS 和 Live2D 两个系统的**关键交汇点**。

**SillyTavern 的实现方式：基于文本时长的参数驱动**

不是基于音频波形的实时分析，而是用简单的正弦波模拟嘴型开合：

```
TTS 音频播放开始
    │
    ▼
获取当前消息的字符数 N
    │
    ▼
计算嘴型动画总时长 = N × time_per_character（用户可配置）
    │
    ▼
启动嘴型动画循环：
    ┌─────────────────────────────────────────┐
    │  while (动画未结束):                      │
    │    mouthOpenY = sin(t × mouth_speed)     │
    │    model.setParameterValue(              │
    │      "PARAM_MOUTH_OPEN_Y", mouthOpenY   │
    │    )                                     │
    │    等待下一帧                              │
    └─────────────────────────────────────────┘
    │
    ▼
动画结束，mouthOpenY 归零
```

关键配置项：

| 参数 | 作用 | 说明 |
|---|---|---|
| `Param mouth open Y id` | 选择嘴部参数 ID | 不同模型命名不同，如 `PARAM_MOUTH_OPEN_Y`、`ParamMouthOpenY` |
| `Mouth movement speed` | 嘴型开合频率 | 控制 sin 波频率，值越大嘴巴开合越快 |
| `Time per character` | 每字符持续时间 | 总动画时长 = 字符数 × 此值 |

**优缺点**：

- ✅ 实现简单，不需要音频分析
- ✅ 跨模型兼容性好（只要有 mouthOpenY 参数）
- ❌ 嘴型与实际语音节奏不同步（只是简单的正弦波）
- ❌ 无法区分元音/辅音的嘴型差异

**更高级的方案：基于 Web Audio API 的实时 PCM 分析**

```javascript
const analyser = audioContext.createAnalyser();
source.connect(analyser);

function updateMouth() {
    const dataArray = new Float32Array(analyser.fftSize);
    analyser.getFloatTimeDomainData(dataArray);

    // 计算 RMS 能量
    let sum = 0;
    for (let i = 0; i < dataArray.length; i++) {
        sum += dataArray[i] * dataArray[i];
    }
    const rms = Math.sqrt(sum / dataArray.length);

    // 映射到嘴型参数
    const mouthOpenY = Math.min(rms * 5, 1.0);
    model.setParameterValue('PARAM_MOUTH_OPEN_Y', mouthOpenY);

    requestAnimationFrame(updateMouth);
}
```

嘴型同步的延迟瓶颈分析：

| 处理阶段 | 典型延迟 | 影响因素 |
|---|---|---|
| 音频解码 (decodeAudioData) | 50-200ms | 文件格式、设备性能 |
| PCM 分析窗口滑动 | 10-50ms | FFT 窗口大小 |
| 嘴型参数计算 | 5-20ms | 算法复杂度 |
| Live2D 参数更新 & 绘制 | 16-33ms (每帧) | 模型复杂度、GPU 性能 |
| **总延迟估算** | **80-300ms** | 超出人耳感知阈值（~70ms） |

### 6.5 表情与动画系统

SillyTavern 的 Live2D 动画调度包含四层：

```
┌─────────────────────────────────────────────────┐
│              动画调度层级                          │
│                                                   │
│  Layer 1: Starter Animation                      │
│  ├── 开始对话时播放                               │
│  ├── 可配置延迟（模型先隐藏再出现）                │
│  └── expression + motion 组合                     │
│                                                   │
│  Layer 2: Default Animation                      │
│  ├── 角色发送消息时播放                           │
│  ├── 作为 Classified Expression 的 fallback       │
│  └── expression + motion 组合                     │
│                                                   │
│  Layer 3: Classified Expression Mapping           │
│  ├── 依赖 classify 扩展识别情绪                   │
│  ├── 每种情绪映射到不同的 expression + motion     │
│  └── 如: "happy" → smile + wave                  │
│                                                   │
│  Layer 4: HitArea Interaction                    │
│  ├── 点击模型不同区域触发不同动画                  │
│  ├── 每个区域可映射 expression + motion + message │
│  └── 如: 点击头部 → 困惑表情 + 歪头 + "怎么了？" │
└─────────────────────────────────────────────────┘
```

**Classify 扩展联动**：SillyTavern 有一个独立的 `classify` 扩展，通过 LLM 分析角色回复的情感倾向（如 happy、sad、angry 等），然后将分类结果传递给 Live2D 扩展，触发对应的表情动画。这形成了一个**情绪驱动的视觉反馈闭环**：

```
LLM 回复文本 → classify 扩展分析情绪 → 映射到 Live2D 表情 → 模型动画播放
```

### 6.6 TTS 与 Live2D 的联动架构

两个系统通过**事件总线**实现联动：

```
                    ┌─────────────────┐
                    │   事件总线        │
                    │  (Event Bus)     │
                    └───────┬─────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
  ┌───────────┐     ┌──────────────┐     ┌───────────┐
  │  TTS 模块  │     │  Live2D 模块  │     │ Chat 模块  │
  │            │     │              │     │           │
  │ on:消息完成│────▶│ on:TTS播放   │     │           │
  │ → 开始播放 │     │ → 嘴型同步   │     │           │
  │            │     │              │     │           │
  │ on:播放结束│────▶│ on:TTS结束   │     │           │
  │            │     │ → 嘴型归零   │     │           │
  │            │     │              │     │           │
  │            │     │ on:情绪分类  │◀────│ → 表情动画│
  └───────────┘     └──────────────┘     └───────────┘
```

完整的一次交互流程：

```
1. 用户发送消息
2. LLM 生成回复（流式文本）
3. 回复完成 → 触发 classify 扩展分析情绪
4. 情绪结果 → Live2D 播放对应表情动画
5. TTS 文本预处理（过滤动作、提取对话）
6. TTS 生成音频 → 开始播放
7. Live2D 启动嘴型同步动画
8. TTS 播放结束 → Live2D 嘴型归零
9. Live2D 回到默认待机动画
```

### 6.7 对 Cos2Edu 的 Live2D 建议

| 特性 | SillyTavern 方案 | Cos2Edu 可借鉴方向 |
|---|---|---|
| Live2D 渲染 | PixiJS + pixi-live2d-display | Vue 3 中通过 `<canvas>` + PixiJS 集成，或用 Vue 组件封装 |
| 嘴型同步 | 基于文本时长的简单正弦波 | 可升级为 Web Audio API 实时 PCM 分析，更自然 |
| 情绪联动 | classify 扩展 → 表情映射 | **Cos2Edu 已有 emotion_engine**，可直接驱动 Live2D 表情 |
| HitArea 交互 | 点击模型区域发送消息 | 教学场景可映射为：点击黑板→展示知识点，点击角色→提问 |
| 模型管理 | 全局 assets + 角色专属目录 | 可复用角色卡导入机制，Live2D 模型作为角色资源的一部分 |

**Cos2Edu 的独有优势**：Cos2Edu 已经有了 `emotion_engine`（情绪引擎），这比 SillyTavern 的 classify 扩展更精确——SillyTavern 需要额外调用 LLM 来分析情绪，而 Cos2Edu 的情绪是实时计算的数值。这意味着 Live2D 的表情驱动可以做到**连续平滑过渡**，而不是离散的表情切换：

```
SillyTavern（离散切换）：
  classify 返回 "happy" → 播放 happy.exp.json → 等待下次分类

Cos2Edu（连续驱动）：
  emotion_engine.mood = 0.82 → mouthOpenY = 0.1, eyeOpenY = 0.9, bodyAngle = 5°
  emotion_engine.mood = 0.75 → mouthOpenY = 0.05, eyeOpenY = 0.85, bodyAngle = 3°
  emotion_engine.mood = 0.60 → mouthOpenY = 0.0, eyeOpenY = 0.7, bodyAngle = 0°
  （每帧更新，平滑过渡）
```

---

## 7. 风险与应对

| 风险点 | 影响 | 应对策略 |
|--------|------|---------|
| 知识条目过多导致上下文溢出 | LLM 输入超长，截断关键信息 | 严格的 token 预算控制 + 优先级排序 + 智能裁剪 |
| 关键词匹配误触发 | 不相关知识被注入，干扰教学 | 次要关键词 + selective_logic 精确控制 + 人工审核 |
| 多角色发言顺序不合理 | 教学逻辑混乱 | 基于教学风格的固定优先级 + 学生情绪动态调整 |
| character_book 维护成本高 | 角色创建门槛升高 | 提供从知识图谱自动生成条目的工具 + 模板库 |
| ST 角色卡导入信息丢失 | 导入后角色缺乏教学能力 | 缺失字段用智能默认值 + 导入后引导用户补充教学配置 |
| TTS 延迟影响教学节奏 | 学生等待时间长，体验差 | 优先使用 EdgeTTS + 按句分段合成 + 预合成缓存 |
| Live2D 模型资源体积大 | 加载慢、占用带宽 | 模型懒加载 + 纹理压缩 + 首屏只加载待机动画 |
| 嘴型同步不自然 | 视觉违和感 | 采用 Web Audio API 实时 PCM 分析替代简单正弦波 |
| emotion_engine 数值到 Live2D 参数的映射不准确 | 表情与情绪不匹配 | 建立情绪维度→Live2D 参数的映射表，支持用户微调 |

---

## 8. 总结

| 问题 | 结论 |
|------|------|
| 角色创建能否参考 ST？ | **参考设计思想，不直接使用**。ST 角色卡缺少教育专属字段，但规范版本控制、扩展字段、内嵌知识库、对话示例等设计值得借鉴 |
| 角色卡能否直接拿来用？ | **不能**。领域模型不匹配，但可实现导入兼容层 |
| 多角色场景互动能否参考世界书？ | **强烈建议参考**。WorldInfo 的关键词触发、注入位置控制、预算管理、时间效应、递归激活等机制，恰好解决了 Cos2Edu 当前最缺乏的"动态知识注入"能力 |
| 最有价值的借鉴点 | ① 精确的上下文注入位置控制（@D深度）② 关键词+向量的双重触发机制 ③ 时间效应（sticky/cooldown/delay）④ 角色过滤（Character Filter）⑤ 预算控制与优先级排序 ⑥ Inclusion Group 互斥机制 |
| Cos2Edu 的独有优势 | ① 结构化知识图谱（非扁平条目）② 显式情感状态机 ③ 师生关系动态模型 ④ 多角色教学协调 ⑤ 学习进度感知的知识注入 |
| TTS 能否参考 ST？ | **参考 Provider 架构，起步用 EdgeTTS**。ST 的多 Provider 策略模式值得借鉴，但教学场景需保留全部文本（非仅引号内容），且语音应直接绑定到角色定义而非全局映射表 |
| Live2D 能否参考 ST？ | **参考渲染架构，升级嘴型同步方案**。ST 的 PixiJS + pixi-live2d-display 方案可直接复用，但嘴型同步应升级为 Web Audio API 实时 PCM 分析；Cos2Edu 的 emotion_engine 可实现连续平滑表情过渡，优于 ST 的离散切换 |
