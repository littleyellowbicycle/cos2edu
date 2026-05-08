# Windows 打包方案

## 一、打包目标

将前后端分离的 Web 项目打包为绿色免安装的 Windows 应用程序：
- **前端**：Vue 构建的静态文件
- **后端**：FastAPI + SQLite
- **用户解压后双击即可运行**，无需安装 Python、Node.js

---

## 二、打包后体积估算

| 组件 | 开发模式 | 打包后 |
|------|----------|--------|
| 前端静态文件 | ~6MB | ~6MB |
| Python 运行时 | N/A | ~40-50MB |
| 后端依赖 | N/A | ~30-50MB |
| PyInstaller 开销 | N/A | ~10-20MB |
| **总计** | - | **约 100-150MB** |

> 注：使用 UPX 压缩可进一步减少 30-50%

---

## 三、项目结构调整

### 3.1 当前结构

```
cos2edu/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   └── services/
│   └── data/
│       └── app.db
└── frontend/
    ├── dist/          # npm run build 产出
    └── src/
```

### 3.2 打包后结构

```
cos2edu/
├── backend/
│   ├── main.py                 # 修改：支持静态文件托管
│   ├── main.spec               # 新增：PyInstaller 配置
│   ├── requirements.txt
│   ├── app/
│   ├── static/                 # 新增：前端构建产物
│   │   ├── index.html
│   │   └── assets/
│   └── data/                   # 运行时创建
│       └── app.db
└── release/                    # 新增：打包输出目录
    └── cos2edu/
        ├── cos2edu.exe
        ├── _internal/         # Python 运行时
        ├── data/              # 可写数据目录
        └── 启动.bat
```

---

## 四、后端修改

### 4.1 创建静态文件托管模块

新建 `backend/app/core/static_files.py`：

```python
import os
import sys
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse


def get_static_dir() -> str:
    """获取静态文件目录（兼容打包模式）"""
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, "static")
    return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static")


def setup_static_files(app):
    """配置静态文件托管"""
    static_dir = get_static_dir()
    
    if not os.path.exists(static_dir):
        return
    
    # 挂载静态资源
    assets_dir = os.path.join(static_dir, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
    
    # SPA 回退
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = os.path.join(static_dir, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(static_dir, "index.html"))
```

### 4.2 修改 main.py

```python
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from slowapi.errors import RateLimitExceeded
import time
import uuid
import sys
import os

from app.core.config import settings
from app.core.database import init_db
from app.core.limiter import limiter
from app.core.logging_config import setup_logging, get_logger
from app.core.static_files import setup_static_files  # 新增
from app.api import api_router

logger = get_logger(__name__)
access_logger = get_logger("access")


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(level=settings.LOG_LEVEL)
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Frozen mode: {getattr(sys, 'frozen', False)}")
    await init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# ... 其他中间件和路由 ...

app.include_router(api_router, prefix="/api/v1", tags=["api-v1"])

# 新增：配置静态文件托管（仅在生产模式）
if not settings.DEBUG:
    setup_static_files(app)


@app.get("/health")
@limiter.limit("60/minute")
async def health(request: Request):
    return {"status": "ok", "name": settings.APP_NAME, "version": settings.APP_VERSION}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
```

### 4.3 修改数据库路径（关键）

修改 `backend/app/core/config.py`，数据库放在用户可写区域：

```python
import os
import sys

def get_data_dir() -> str:
    """获取数据目录（兼容打包模式）"""
    if getattr(sys, 'frozen', False):
        app_data = os.getenv("APPDATA")
        app_dir = os.path.join(app_data, "cos2edu")
        os.makedirs(app_dir, exist_ok=True)
        return app_dir
    return "./data"


class BaseConfig(BaseSettings):
    # ... 其他配置 ...
    
    DATA_DIR: str = get_data_dir()  # 修改：动态获取
    DATABASE_URL: str = f"sqlite+aiosqlite:///{os.path.join(get_data_dir(), 'app.db')}"
    
    # 目录路径也要用 DATA_DIR
    CHARACTERS_DIR: str = os.path.join(get_data_dir(), "characters")
    MATERIALS_DIR: str = os.path.join(get_data_dir(), "materials")
    CONVERSATIONS_DIR: str = os.path.join(get_data_dir(), "conversations")
    UPLOADS_DIR: str = os.path.join(get_data_dir(), "uploads")
    AVATARS_DIR: str = os.path.join(get_data_dir(), "uploads", "avatars")
    BACKGROUNDS_DIR: str = os.path.join(get_data_dir(), "uploads", "backgrounds")
```

---

## 五、打包配置

### 5.1 创建 PyInstaller spec 文件

新建 `backend/main.spec`：

```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('static', 'static'),  # 前端构建产物
    ],
    hiddenimports=[
        'sqlalchemy.sql.default_comparator',
        'aiosqlite',
        'uvicorn',
        'starlette',
        'fastapi',
        'pydantic',
        'slowapi',
        'httpx',
        'jinja2',
        'python_multipart',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        'numpy', 'pandas', 'matplotlib', 'tkinter',
        'test', 'tests', 'pytest', 'scipy'
    ],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='cos2edu',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # 不显示命令行窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='cos2edu',
)
```

### 5.2 打包步骤

```bash
# 1. 进入后端目录
cd backend

# 2. 构建前端
cd ../frontend && npm run build && cd ../backend

# 3. 复制前端构建产物到 static 目录
mkdir -p static
cp -r ../frontend/dist/* static/

# 4. 安装 PyInstaller（如果未安装）
pip install pyinstaller

# 5. 下载 UPX（可选，用于压缩）
# 将 upx.exe 放到 backend 目录或 PATH 中

# 6. 执行打包
pyinstaller main.spec --upx-dir=.

# 7. 创建数据目录（运行时自动创建，但可预先创建空目录）
mkdir -p dist/cos2edu/data

# 8. 创建启动脚本
```

### 5.3 创建启动脚本

在 `dist/cos2edu/` 下创建 `启动.bat`：

```bat
@echo off
chcp 65001 >nul
title 苏格拉底AI教学系统

echo 正在启动苏格拉底AI教学系统...
echo.

start "" "cos2edu.exe"

echo 正在打开浏览器...
timeout /t 3 /nobreak >nul
start http://127.0.0.1:8000

echo 启动完成！
pause
```

---

## 六、打包脚本

创建自动化打包脚本 `backend/build.bat`：

```bat
@echo off
chcp 65001 >nul
setlocal

echo ===== 苏格拉底AI教学系统 打包工具 =====
echo.

cd /d "%~dp0"

REM 检查前端目录
if not exist "..\frontend\dist" (
    echo [错误] 前端构建产物不存在！
    echo 请先运行: cd ..\frontend ^&^& npm run build
    pause
    exit /b 1
)

REM 清理旧构建
echo [1/5] 清理旧构建...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build
if exist "*.spec" del /q *.spec
if exist "cos2edu.spec" del /q cos2edu.spec

REM 复制前端构建产物
echo [2/5] 复制前端构建产物...
if exist "static" rmdir /s /q static
mkdir static
xcopy /e /y "..\frontend\dist\*" "static\"

REM 检查 UPX
echo [3/5] 检查 UPX...
set UPX_DIR=
if exist "upx.exe" set UPX_DIR=.
where upx >nul 2>&1
if %errorlevel% equ 0 set UPX_DIR=

REM 执行打包
echo [4/5] 执行 PyInstaller 打包...
if defined UPX_DIR (
    pyinstaller --noconfirm --clean --onedir --upx-dir="%UPX_DIR%" main.py
) else (
    pyinstaller --noconfirm --clean --onedir main.py
)

REM 复制启动脚本
echo [5/5] 创建启动脚本...
if exist "dist\cos2edu" (
    echo @echo off > "dist\cos2edu\启动.bat"
    echo chcp 65001 ^>nul >> "dist\cos2edu\启动.bat"
    echo title 苏格拉底AI教学系统 >> "dist\cos2edu\启动.bat"
    echo start "" "cos2edu.exe" >> "dist\cos2edu\启动.bat"
    echo timeout /t 3 /nobreak ^>nul >> "dist\cos2edu\启动.bat"
    echo start http://127.0.0.1:8000 >> "dist\cos2edu\启动.bat"
)

echo.
echo ===== 打包完成！=====
echo 输出目录: dist\cos2edu
echo.
echo 启动方式: 双击"启动.bat"
echo.

endlocal
pause
```

---

## 七、交付物结构

用户解压后获得：

```
cos2edu/
├── cos2edu.exe           # 主程序
├── 启动.bat               # 一键启动脚本
├── _internal/             # Python 运行时和依赖
│   ├── python.exe
│   ├── python3.dll
│   ├── DLLs/
│   └── Lib/
├── data/                  # 用户数据目录（运行时创建）
│   ├── app.db            # SQLite 数据库
│   ├── characters/
│   ├── materials/
│   ├── conversations/
│   └── uploads/
└── venv/                  # （如有）虚拟环境
```

---

## 八、进一步优化

### 8.1 减小体积

| 优化项 | 效果 | 方法 |
|--------|------|------|
| UPX 压缩 | -30%~50% | 下载 UPX 并在打包时使用 `--upx-dir` |
| 排除不需要的模块 | -10~20MB | 在 spec 的 `excludes` 中添加 |
| 精简依赖 | -5~10MB | 只导入需要的库 |

### 8.2 排除的模块

```python
excludes=[
    'numpy',      # 不使用
    'pandas',     # 不使用
    'matplotlib', # 不使用
    'tkinter',    # GUI 不需要
    'test',       # 测试框架
    'tests',
    'pytest',
    'scipy',      # 不使用
    'PIL',        # 如不需要图片处理
]
```

### 8.3 使用虚拟环境

确保打包的依赖干净：

```bash
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
pip install pyinstaller upx
pyinstaller main.spec
```

---

## 九、注意事项

### 9.1 路径问题

- 使用 `sys._MEIPASS` 检测是否在打包模式
- 数据库路径必须使用 `%APPDATA%`，否则打包后无法写入

### 9.2 依赖问题

- `hiddenimports` 中添加动态导入的模块
- 如遇缺少模块错误，添加到 `hiddenimports`

### 9.3 端口问题

- 默认使用 8000 端口
- 如需修改，修改 `config.py` 中的 `PORT`

### 9.4 图标（可选）

添加自定义图标：

```python
exe = EXE(
    # ...
    icon='app.ico',  # 添加图标
)
```

---

## 十、常见问题

### Q1: 打包后运行报错 "ModuleNotFoundError"

将缺失的模块添加到 `hiddenimports`：

```python
hiddenimports=[
    '缺失的模块名',
    # ...
]
```

### Q2: 前端静态文件加载失败

检查：
1. `static/` 目录是否正确复制
2. `get_static_dir()` 返回路径是否正确
3. `app.mount()` 是否正确配置

### Q3: 数据库写入失败

确保：
1. 数据库路径在 `%APPDATA%` 下
2. 目录已创建（`os.makedirs(exist_ok=True)`）

### Q4: 启动闪退

添加 `console=True` 重新打包，查看错误信息。

---

## 十一、后续任务

- [ ] 修改 `config.py` 支持动态数据目录
- [ ] 创建 `static_files.py` 托管模块
- [ ] 修改 `main.py` 调用静态文件配置
- [ ] 创建 `main.spec` PyInstaller 配置
- [ ] 创建 `build.bat` 自动化打包脚本
- [ ] 测试打包后程序运行
- [ ] 优化打包体积