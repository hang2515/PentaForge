@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo   PentaForge - 启动项目
echo ========================================

if not exist ".venv\Scripts\python.exe" (
    echo [错误] 未找到 .venv，请先运行 LOCAL_SETUP.md 的首次安装步骤
    pause
    exit /b 1
)

where npm >nul 2>nul
if errorlevel 1 (
    echo [错误] 未找到 npm，请先安装 Node.js 20 或更新版本
    pause
    exit /b 1
)

if not exist "pentaforge\web\node_modules" (
    echo [错误] 未找到前端依赖 node_modules，请先运行:
    echo cd pentaforge\web
    echo npm install
    pause
    exit /b 1
)

echo [1/2] 启动后端 (127.0.0.1:8000)...
start "PentaForge Backend" ".venv\Scripts\python.exe" -m uvicorn src.server:app --app-dir pentaforge --host 127.0.0.1 --port 8000 --reload

echo [2/2] 启动前端 (127.0.0.1:5173)...
start "PentaForge Frontend" cmd /c "cd /d pentaforge\web && npm run dev -- --host 127.0.0.1"

echo.
echo 后端: http://127.0.0.1:8000
echo 前端: http://127.0.0.1:5173
echo.
echo 按任意键关闭此窗口...
pause >nul
