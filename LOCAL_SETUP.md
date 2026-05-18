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

## 六、安装 OCR 自动识别依赖

默认依赖不包含 OCR 引擎，因为 PaddleOCR 会额外安装 PaddlePaddle，体积较大。

如果需要使用“从当前视频自动识别”功能，再执行：

```powershell
.\.venv\Scripts\python.exe -m pip install -r .\pentaforge\requirements-ocr.txt
```

当前已验证可用组合：Python 3.13、`paddlepaddle 3.3.1`、`paddleocr 3.5.0`。

安装后可以先做一次自检：

```powershell
.\.venv\Scripts\python.exe -c "import paddle; paddle.utils.run_check(); from paddleocr import PaddleOCR; print('PaddleOCR import ok')"
```

自检通过后重启后端服务，再在 Web 页面中使用“自动识别候选”面板。

如果 PaddlePaddle 安装失败，优先使用 Python 3.11 或 3.12 重新创建 `.venv`；OCR 依赖对 Python 版本和平台轮子更敏感。

## 七、常见问题

如果提示找不到 `python`，说明 Python 没有加入系统 PATH，重新安装 Python 时勾选 `Add Python to PATH`。

如果提示找不到 `npm`，说明 Node.js 没有安装成功，或没有加入系统 PATH。

如果前端页面能打开但接口报错，确认后端 `127.0.0.1:8000` 是否正在运行。

如果是从 Git 重新拉取项目，`node_modules` 和 `.venv` 不会被提交，需要重新执行首次安装依赖步骤。
