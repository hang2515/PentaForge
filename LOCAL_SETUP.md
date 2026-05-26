# PentaForge 本地运行说明

本项目不使用 Docker 时，可以直接在本机运行：

- 后端使用 Python 虚拟环境 `.venv`
- 前端使用 Node.js 安装 Vue/Vite 依赖

适合从 Git 拉取项目后，在新电脑上快速恢复开发和运行环境。

## 一、需要先安装的软件

新电脑需要先安装：

- Python 3.11 或更新版本
- Node.js 20 或更新版本
- Git

后端依赖里包含 `imageio-ffmpeg`，通常会自动安装可用的 FFmpeg 二进制文件，所以大多数情况下不需要单独安装系统 FFmpeg。

## 二、首次安装依赖

在项目根目录执行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
.\.venv\Scripts\python.exe -m pip install -r .\pentaforge\requirements-dev.txt

cd .\pentaforge\web
npm install
cd ..\..
```

说明：

- `.venv` 是 Python 后端虚拟环境
- `requirements-dev.txt` 会安装运行依赖和测试依赖
- `npm install` 会安装前端依赖，生成 `node_modules`

## 三、开发模式启动

### 方式 A：使用启动脚本

完成首次安装依赖后，可以直接双击或在 PowerShell 中运行：

```powershell
.\start.bat
```

脚本会启动：

- 后端：`http://127.0.0.1:8000`
- 前端：`http://127.0.0.1:5173`

脚本会检查：

- `.venv\Scripts\python.exe` 是否存在
- `npm` 是否可用
- `pentaforge\web\node_modules` 是否存在

如果检查失败，按提示先执行首次安装依赖步骤。

### 方式 B：手动启动两个终端

开发模式需要开两个终端。

第一个终端，在项目根目录启动后端：

```powershell
.\.venv\Scripts\python.exe -m uvicorn src.server:app --app-dir .\pentaforge --host 127.0.0.1 --port 8000
```

第二个终端，启动前端：

```powershell
cd .\pentaforge\web
npm run dev -- --host 127.0.0.1
```

然后打开：

```text
http://127.0.0.1:5173
```

前端开发服务器会把 `/api` 和 `/ws` 请求代理到后端：

```text
http://127.0.0.1:8000
```

## 四、构建前端并由后端直接访问

如果不想同时开前端开发服务器，可以先构建前端：

```powershell
cd .\pentaforge\web
npm run build
cd ..\..
```

然后只启动后端：

```powershell
.\.venv\Scripts\python.exe -m uvicorn src.server:app --app-dir .\pentaforge --host 127.0.0.1 --port 8000
```

打开：

```text
http://127.0.0.1:8000
```

## 五、运行测试

在项目根目录执行：

```powershell
$env:PYTHONPATH = (Resolve-Path -LiteralPath .\pentaforge).Path
.\.venv\Scripts\python.exe -m pytest .\pentaforge\tests -q
```

## 六、OCR 自动识别依赖

PaddleOCR 已包含在 `requirements.txt` 中，随主依赖一起安装。

当前已验证可用组合：Python 3.13、`paddlepaddle 3.3.1`、`paddleocr 3.5.0`。

安装后可以先做一次自检：

```powershell
.\.venv\Scripts\python.exe -c "import paddle; paddle.utils.run_check(); from paddleocr import PaddleOCR; print('PaddleOCR import ok')"
```

自检通过后重启后端服务，再在 Web 页面中使用“自动识别候选”面板。

当前 Web 页面中有两个 OCR 入口：

- `从当前视频自动识别`：识别多杀事件并生成候选片段，用户可以手动添加和调整。
- `一键识别五杀并导出`：识别包含五杀的多杀链，自动生成五杀片段并启动导出任务。

默认 OCR 参数：

```text
采样间隔：0.5 秒
最低置信度：0.3
ROI：x=0.2, y=0.06, width=0.6, height=0.24
双杀前推：15 秒
五杀后留尾：3 秒
多杀链最大间隔：12 秒
```

如果 PaddlePaddle 安装失败，优先使用 Python 3.11 或 3.12 重新创建 `.venv`；OCR 依赖对 Python 版本和平台轮子更敏感。

## 七、常见问题

如果提示找不到 `python`，说明 Python 没有加入系统 PATH，重新安装 Python 时勾选 `Add Python to PATH`。

如果提示找不到 `npm`，说明 Node.js 没有安装成功，或没有加入系统 PATH。

如果前端页面能打开但接口报错，确认后端 `127.0.0.1:8000` 是否正在运行。

如果是从 Git 重新拉取项目，`node_modules` 和 `.venv` 不会被提交，需要重新执行首次安装依赖步骤。
