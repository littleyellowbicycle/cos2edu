# 桌面版打包方案

> 文档版本：v0.1（草稿）
> 日期：2026-07-09
> 状态：待讨论

---

## 一、当前代码库桌面化现状

### 1.1 已就绪

| 组件 | 文件路径 | 说明 |
|------|---------|------|
| PyInstaller spec | `packaging/main.spec` | 含完整 hiddenimports，excludes numpy/pandas/scipy 等 |
| 构建脚本 | `packaging/build.bat` | 自动化：构建前端 → 复制静态 → PyInstaller → 输出到 dist/ |
| 静态文件托管 | `backend/app/core/static_files.py` | `get_static_dir()` 兼容 `sys.frozen` 模式，自动查找 multi-location |
| 数据目录抗冻 | `backend/app/core/config.py` | `get_data_dir()` 在 frozen 模式下走 `%APPDATA%/cos2edu` |
| 初始化链路 | `backend/main.py` | 已调用 `setup_static_files(app)`，日志输出 `is_production_mode()` |
| Generative UI 组件 | `frontend/src/components/generative/` | DynamicRenderer · EmotionCard · QuizForm · Timeline · KnowledgeGraph · SceneCard |
| Chat 子组件拆分 | `frontend/src/components/chat/` | ChatHeader · ChatMessages · MessageBubble · MarkdownContent · ChatInput · ChatSidebar · TypingIndicator |

### 1.2 缺失

| 组件 | 现状 | 影响 |
|------|------|------|
| Tauri shell | `frontend/src-tauri/` 不存在 | 无原生窗口 |
| App Icon / Favicon | `public/` 不存在，`index.html` 无 `<link rel="icon">` | 打包后无图标 |
| 全局导航栏 | 各视图独立，无 persistent navbar | Tauri 中跨视图需依赖浏览器式跳转 |
| CI/CD 构建脚本 | `.github/workflows/` 不存在 | 无法自动化跨平台构建 |
| Windows 数字签名 | 无签名证书 | 发布后 SmartScreen 可能拦截 |

---

## 二、两方案对比

| 维度 | **方案 A：纯 PyInstaller** | **方案 B：Tauri + PyInstaller Sidecar** |
|------|---------------------------|----------------------------------------|
| 实现周期 | 1–2 天 | 3–5 天 |
| 最终用户获得 | 文件夹 + `启动.bat` → 浏览器打开 | `.msi` 安装包 → 原生窗口（无浏览器 chrome） |
| 安装流程 | 解压 → 双击 bat | 双击 msi → 桌面快捷方式 |
| 单文件体积 | ~150 MB（含 Python 运行时） | ~5 MB（Tauri 壳）+ ~150 MB（sidecar）= ~155 MB |
| 自动更新 | 需手写 | Tauri 内置（GitHub Releases） |
| 难点 | spec 的 hiddenimports 要精准 | Rust 编译环境 + sidecar 进程管理 |
| 用户感知 | "绿色版工具" — 够用 | "正式桌面软件" — 更专业 |

### 推荐路径：分两步走

```
Step 1（本项目） →  纯 PyInstaller 跑通验证
Step 2（下一阶段） →  Tauri 加壳，生成安装器
```

---

## 三、Step 1：纯 PyInstaller 打包

### 3.1 当前打包流程

```
          ┌──────────────────────┐
          │  frontend/npm build   │
          │  → frontend/dist/     │
          └──────────┬───────────┘
                     │ xcopy
                     ▼
          ┌──────────────────────┐
          │  backend/static/     │
          │  (index.html+assets) │
          └──────────┬───────────┘
                     │
          ┌──────────────────────┐
          │  PyInstaller         │
          │  main.spec → exe     │
          └──────────┬───────────┘
                     │
          ┌──────────────────────┐
          │  release/cos2edu/    │
          │  ├── cos2edu.exe     │
          │  ├── _internal/      │
          │  └── 启动.bat        │
          └──────────────────────┘
```

### 3.2 已有打包配置

| 文件 | 路径 | 关键逻辑 |
|------|------|---------|
| `main.spec` | `packaging/main.spec:1` | Analysis → hiddenimports 含 `fastapi`, `uvicorn`, `sqlalchemy`, `aiosqlite` 等 |
| | | EXE: `console=False`, `upx=True` |
| | | COLLECT: `onedir` 模式 |
| `build.bat` | `packaging/build.bat:129` | 步骤: clean → copy static → copy spec → pyinstaller → move dist → create data dirs → create 启动.bat |

### 3.3 待办项

- [ ] **核对 `backend/requirements.txt` 中的 `faiss-cpu` / `sentence-transformers` 是否被代码引用**，若未被引用则从依赖中移除，减少 ~30MB 体积
- [ ] **在当前开发机上执行 `packaging\build.bat`**，暴露缺失的 hiddenimports
- [ ] **将 `main.spec` 从 `packaging/` 移至 `backend/` 根目录**（CI 流更自然）
- [ ] **补充缺失的 hiddenimports**，反复打包直至运行无报错
- [ ] **测试 8000 端口被占用时的兜底逻辑**，若无则添加自动找空闲端口的机制

### 3.4 输出物结构

```
release/cos2edu-v1.0.0/
├── cos2edu.exe              # 主程序（双击启动后端）
├── 启动.bat                  # 一键启动（启动后端 + 打开浏览器）
│
├── _internal/               # Python 运行时 + 依赖（~150 MB）
│   ├── python3.dll
│   ├── python311.dll
│   ├── DLLs/
│   └── Lib/
│
└── data/                    # 运行时自动创建（实际在 %APPDATA%/cos2edu）
    ├── app.db               # SQLite 数据库
    ├── characters/
    ├── materials/
    ├── conversations/
    └── uploads/
```

---

## 四、Step 2：Tauri 桌面壳

### 4.1 初始化

```bash
cd frontend
npm install -D @tauri-apps/cli@latest
npx tauri init
```

### 4.2 tauri.conf.json 配置

```jsonc
{
  "productName": "Cos²Edu",
  "version": "1.0.0",
  "identifier": "com.cos2edu.app",
  "build": {
    "frontendDist": "../dist",
    "devUrl": "http://localhost:5173",
    "beforeBuildCommand": "npm run build"
  },
  "app": {
    "windows": [
      {
        "title": "Cos²Edu — 苏格拉底 AI 教学系统",
        "width": 1200,
        "height": 800,
        "minWidth": 900,
        "minHeight": 600,
        "resizable": true,
        "decorations": true,     // 保留原生标题栏
        "center": true
      }
    ],
    "security": {
      "csp": "default-src 'self'; connect-src 'self' http://localhost:8000 ws://localhost:8000; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: http://localhost:8000;"
    }
  },
  "bundle": {
    "active": true,
    "targets": "msi",
    "icon": [
      "icons/32x32.png",
      "icons/128x128.png",
      "icons/128x128@2x.png",
      "icons/icon.ico"
    ]
  }
}
```

### 4.3 Sidecar 进程管理（Rust）

```
┌───── Tauri main (Rust) ───────────────────────────┐
│                                                     │
│  setup() ──────────────────────────────────┐        │
│  │                                            │        │
│  │  spawn("sidecar/cos2edu.exe")  ← PyInstaller exe  │
│  │  │                                            │        │
│  │  └─ ping http://localhost:8000/health ──┐       │
│  │       ┌─ retry 10×, interval 500ms      │       │
│  │       └─ ready → load WebView ──────┐      │       │
│  │                                         │      │       │
│  on_window_event(CloseRequested) ────┐    │      │       │
│  ├─ 向 sidecar 发 graceful shutdown    │    │      │       │
│  ├─ 等待 5s                            │    │      │       │
│  └─ kill sidecar                       │    │      │       │
│                                         ▼    ▼      │       │
│  ┌── WebView ────────────────────────┐            │       │
│  │  http://localhost:5173 (dev)        │            │       │
│  │  file://dist/index.html (prod)     │            │       │
│  └────────────────────────────────────┘            │       │
└──────────────────────────────────────────────────────┘
```

核心代码骨架（`src-tauri/src/main.rs`）：

```rust
fn main() {
    tauri::Builder::default()
        .setup(|app| {
            // 1. 获取 sidecar 资源路径
            let sidecar = app.path().resource_dir()
                .unwrap().join("binaries").join("cos2edu.exe");

            // 2. spawn 后端进程
            let (mut rx, child) = app.shell().sidecar("cos2edu")
                .unwrap().spawn().expect("Failed to start backend");

            // 3. 轮询 health endpoint 等待就绪
            let client = reqwest::blocking::Client::new();
            for _ in 0..10 {
                std::thread::sleep(Duration::from_millis(500));
                if client.get("http://localhost:8000/health").send().is_ok() {
                    break;
                }
            }

            // 4. 窗口关闭时 kill 后端
            app.on_window_event(move |event| {
                if let tauri::WindowEvent::CloseRequested { .. } = event {
                    let _ = child.kill();
                }
            });

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

### 4.4 构建与签名

```bash
cd frontend
npm run tauri build

# 输出:
# src-tauri/target/release/bundle/msi/Cos2Edu_1.0.0_x64.msi
```

**Windows 数字签名**（绕过 SmartScreen 拦截）：
```bash
# 购买证书后（如 DigiCert / Sectigo）：
signtool sign /fd SHA256 /a /f mycert.pfx /p mypassword /tr http://timestamp.digicert.com /td SHA256 "Cos2Edu_1.0.0_x64.msi"
```

---

## 五、Tauri 界面设计

### 5.1 窗口布局

```
┌── 原生系统标题栏 (decorations: true) ──────────────────┐
│  ┌ 全局导航栏（新增）────────────────────────────────── ┐   │
│  │                                                        │   │
│  │   ❧  Cos²Edu    首页 · 角色 · 对话 · 课程 · 设置       │   │
│  │                                                        │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌ 当前视图内容 ───────────────────────────────────────────┐  │
│  │                                                          │  │
│  │  各视图独立渲染（保持不变）                                │  │
│  │                                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

**窗口参数：**
- 尺寸：`1200 × 800`
- 最小尺寸：`900 × 600`
- 居中启动，可缩放
- 保留原生系统标题栏（`decorations: true`）

### 5.2 为什么需要全局导航栏？

当前网页版可以通过浏览器地址栏输入 `/characters`、`/chat/xxx` 跳转。Tauri 窗口没有地址栏，因此需要一条 persistent 导航栏来实现页面切换：

| 菜单项 | 路由 | 图标 |
|--------|------|------|
| 首页 | `/` | ❧ |
| 角色 | `/characters` | 🧑‍🏫 |
| 对话 | `/conversations` | 💬 |
| 课程 | `/curriculum` | 📚 |
| 设置 | `/settings` | ⚙️ |

**样式方案**（基于现有 CSS 变量）：

```
导航栏容器：
  background: var(--color-bg-warm)    /* #F5F1EB */ 
  border-bottom: 1px solid var(--color-border)  /* #E5E0D8 */
  height: 52px
  padding: 0 24px

导航项（非选中）：
  color: var(--color-text-muted)    /* #6B6B6B */
  font-family: var(--font-body)
  font-size: 14px
  padding: 0 16px

导航项（选中/悬停）：
  color: var(--color-accent)        /* #8B4513 */
  border-bottom: 2px solid var(--color-accent)
```

### 5.3 App Icon 设计建议

以 ❧ 符号为核心视觉元素：

```
┌──────────┐
│          │
│   #FFF   │  底色：var(--color-accent)  #8B4513（暖棕）
│    ❧    │  图形：白色 ❧，粗体，居中
│          │  形状：圆角方形，24px radius
│          │  分辨率：1024×1024（导出多尺寸）
└──────────┘

衍生尺寸：
  32×32    → src-tauri/icons/32x32.png
  128×128  → src-tauri/icons/128x128.png
  256×256  → src-tauri/icons/128x128@2x.png
  256×256  → src-tauri/icons/icon.ico（Windows .ico 格式）
  512×512  → 用于微软商店
```

### 5.4 不需要重写即可直接嵌入的部分

| 页面 | 当前状态 | 在 Tauri 中表现 |
|------|---------|---------------|
| Chat.vue（1200px 布局） | Sidebar 300px 默认隐藏 | 展开后 1200 - 300 = 900，刚好 |
| Home.vue | Hero + FeatureCard 网格 | 原生窗口全屏效果更好 |
| Curriculum.vue | Mermaid 脑图 | 桌面大屏下阅读体验提升 |
| 其余页面 | 标准 table/card 布局 | 无需改动 |

### 5.5 需要修改的部分

| 问题 | 原因 | 修改方案 |
|------|------|---------|
| 无全局导航栏 | 各视图独立 | 新增 `AppNav.vue` 组件，在 `App.vue` 中引入 |
| 无 favicon/app icon | `index.html` 无 `link[rel=icon]` | 新增 `public/favicon.ico` + `public/logo.svg` |
| 路由模式 | `createWebHistory()` | Tauri 中正常工作 |
| 右键行为 | 浏览器右键菜单 | 在 `<router-view>` 外层阻止默认右键菜单 |
| 外部链接 | 若有点击会打开系统浏览器 | 使用 `tauri::api::shell::open` |

---

## 六、关键风险与应对

| 风险 | 影响 | 应对 |
|------|------|------|
| `faiss-cpu` 打包后 ~30MB | 体积膨胀 | 确认是否被代码引用，若未引用则移除 |
| `sentence-transformers` 需要下载模型 | 模型 ~400MB+，不能打包 | 改为首次启动按需下载，或换轻量 embedding |
| 8000 端口被占用 | 后端启动失败 | 添加自动端口检测 + fallback 端口 + 前端自动同步 |
| SmartScreen 拦截 | 用户不敢运行 | 购买代码签名证书（DigiCert ~$300/年） |
| Tauri Rust 环境 | 首次搭建需 1–2h | 只需要一人装 Rust 工具链，CI 可以复用 |
| 路径编码 (sys._MEIPASS) | Windows 上中文路径可能异常 | `get_static_dir()` 已做 os.path.realpath |
| 多语言/CSP 策略 | 字体 CDN 被拦截 | 在 CSP 中显式 allow `fonts.gstatic.com` / `fonts.googleapis.com` |

---

## 七、需用户确认的问题

- [ ] **全局导航栏 — 要不要加？** 不加的话，用户只能通过首页按钮跳转；加的话需要设计样式（文档已有建议方案）
- [ ] **App Icon — ❧ 作为主视觉？** 延续品牌识别，暖棕底 `#8B4513` + 白色 ❧
- [ ] **自定义标题栏 — 要做吗？** 不做省事（`decorations: true`），做的话仿 Windows 11 圆角，但需多 ~2 天
- [ ] **打包顺序 — 先跑通 Step 1 再进 Step 2？** 建议分步，阻隔复杂度

---

## 附录：引用文件

| 文件 | 路径 | 用途 |
|------|------|------|
| PyInstaller config | `packaging/main.spec` | 打包配置文件 |
| 构建脚本 | `packaging/build.bat` | Windows 自动化打包脚本 |
| 后端入口 | `backend/main.py` | FastAPI 启动 + 引擎初始化 |
| 静态文件托管 | `backend/app/core/static_files.py` | 生产模式静态资源路由 |
| 数据目录配置 | `backend/app/core/config.py` | `get_data_dir()` 路径抗冻逻辑 |
| 现有打包文档 | `docs/Windows打包方案.md` | 上一版打包方案说明 |
| 后端依赖清单 | `backend/requirements.txt` | 需核对的 Python 依赖包 |