# Windows 打包说明

## 打包前准备

### 1. 安装依赖

```bash
# 进入后端目录安装依赖
cd ../backend
pip install -r requirements.txt
pip install pyinstaller

# (可选) 下载 UPX 压缩工具，进一步减小体积 30-50%
# 下载地址: https://github.com/upx/upx/releases
# 将 upx.exe 放到 backend 或 packaging 目录
```

### 2. 安装 Node.js（用于构建前端）

访问 https://nodejs.org/ 下载安装。

---

## 打包步骤

### 方法一：使用打包脚本（推荐）

```bash
cd packaging
.\build.bat
```

### 方法二：手动打包

```bash
# 1. 构建前端
cd ../frontend
npm run build

# 2. 复制前端构建产物到 static 目录
cd ../backend
mkdir static
xcopy /e /y "..\frontend\dist\*" "static\"

# 3. 回到 packaging 目录
cd ../packaging

# 4. 执行 PyInstaller 打包
pyinstaller --noconfirm --clean --onedir --upx-dir=. main.spec
```

---

## 打包产物

打包完成后，产物在 `packaging/dist/cos2edu/` 目录：

```
cos2edu/
├── cos2edu.exe           # 主程序
├── 启动.bat              # 一键启动脚本
├── _internal/            # Python 运行时
├── data/                 # 用户数据目录（运行时创建）
│   ├── app.db           # SQLite 数据库
│   ├── characters/
│   ├── materials/
│   ├── conversations/
│   └── uploads/
└── ...
```

---

## 启动方式

1. **方式一**：双击 `启动.bat`
2. **方式二**：直接运行 `cos2edu.exe`，然后手动打开浏览器访问 http://127.0.0.1:8000

---

## 常见问题

### Q1: 打包后运行报错 ModuleNotFoundError

将缺失的模块添加到 `main.spec` 的 `hiddenimports` 列表中。

### Q2: 前端静态文件加载失败

检查 `backend/static` 目录是否包含前端构建产物。

### Q3: 数据库写入失败

确保用户有 `AppData\cos2edu` 目录的写权限。

### Q4: 端口被占用

修改 `app/core/config.py` 中的 `PORT` 配置。

---

## 体积优化

| 优化项 | 效果 |
|--------|------|
| 启用 UPX | -30%~50% |
| 排除不需要的模块 | -10~20MB |
| 按需导入依赖 | -5~10MB |

---

## 技术支持

如遇问题，请检查：
1. Python 版本（推荐 3.10+）
2. 所有依赖是否正确安装
3. 杀毒软件是否拦截