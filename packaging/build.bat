@echo off
chcp 65001 >nul
setlocal

echo ===== 苏格拉底AI教学系统 打包工具 =====
echo.

cd /d "%~dp0"
set PACKAGE_DIR=%cd%

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

REM 复制前端构建产物到 backend/static
echo [2/5] 复制前端构建产物到 backend/static...
if exist "..\backend\static" rmdir /s /q "..\backend\static"
mkdir "..\backend\static"
xcopy /e /y "..\frontend\dist\*" "..\backend\static\"
if %errorlevel% neq 0 (
    echo [错误] 复制前端构建产物失败！
    pause
    exit /b 1
)

REM 检查 UPX
echo [3/5] 检查 UPX...
set UPX_DIR=
where upx >nul 2>&1
if %errorlevel% equ 0 (
    set UPX_DIR=.
    echo [信息] 找到 UPX，将启用压缩
) else (
    echo [信息] 未找到 UPX，跳过压缩
    echo [提示] 下载 UPX 可进一步减小体积 30-50%%
    echo [提示] 访问: https://upx.github.io/
)

REM 执行打包
echo.
echo [4/5] 复制打包配置到 backend 目录...
copy /y "main.spec" "..\backend\main.spec" >nul 2>&1

echo [5/5] 执行 PyInstaller 打包...
echo 此过程可能需要几分钟，请耐心等待...
echo.

cd /d "%~dp0\..\backend"
if defined UPX_DIR (
    pyinstaller --noconfirm --clean --onedir --upx-dir="%UPX_DIR%" main.spec
) else (
    pyinstaller --noconfirm --clean --onedir main.spec
)

if %errorlevel% neq 0 (
    echo.
    echo [错误] 打包失败！
    pause
    exit /b 1
)

REM 回到 packaging 目录
cd /d "%PACKAGE_DIR%"

REM 移动打包产物
echo.
echo [完成] 整理打包产物...
if exist "..\backend\dist\cos2edu" (
    move /y "..\backend\dist\cos2edu" "dist\cos2edu" >nul 2>&1
    if not exist "dist\cos2edu" mkdir "dist\cos2edu"
    move /y "..\backend\dist\cos2edu" "dist\" 2>nul
)

REM 创建数据目录
if exist "dist\cos2edu" (
    mkdir "dist\cos2edu\data" 2>nul
    mkdir "dist\cos2edu\data\characters" 2>nul
    mkdir "dist\cos2edu\data\materials" 2>nul
    mkdir "dist\cos2edu\data\conversations" 2>nul
    mkdir "dist\cos2edu\data\uploads" 2>nul
    mkdir "dist\cos2edu\data\uploads\avatars" 2>nul
    mkdir "dist\cos2edu\data\uploads\backgrounds" 2>nul
)

REM 创建启动脚本
echo [完成] 创建启动脚本...
if exist "dist\cos2edu" (
    (
        echo @echo off
        echo chcp 65001 ^>nul
        echo title 苏格拉底AI教学系统
        echo.
        echo echo 正在启动苏格拉底AI教学系统...
        echo echo.
        echo start "" "cos2edu.exe"
        echo.
        echo echo 正在打开浏览器...
        echo timeout /t 3 /nobreak ^>nul
        echo start http://127.0.0.1:8000
        echo.
        echo echo 启动完成！
        echo pause
    ) > "dist\cos2edu\启动.bat"
)

REM 清理临时文件
del /q "..\backend\main.spec" 2>nul

echo.
echo ===== 打包完成！=====
echo.
echo 输出目录: %PACKAGE_DIR%\dist\cos2edu
echo.
echo 启动方式: 双击"启动.bat" 或直接运行 cos2edu.exe
echo.
echo 提示: 首次运行会自动创建数据目录和数据库
echo.

endlocal
pause