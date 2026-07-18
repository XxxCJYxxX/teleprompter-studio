# 提词器 · Teleprompter Studio

<div align="center">

**一个零依赖、即开即用的 Web 提词器，支持单机/双端两种模式**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)

### 🚀 [点我直接使用 → teleprompter-studio](https://xxxcjyxxx.github.io/teleprompter-studio/)

</div>

---

## 📖 这是什么

一个开箱即用的中文提词器工具，专为视频拍摄、直播、演讲场景设计。提供两种使用方式：

| 模式 | 文件 | 适合 |
|------|------|------|
| **单机版** | `teleprompter.html` | 一个人拍摄，笔记本/平板当提词器 |
| **双端版** | `prompter-server.py` | 导演在笔记本编辑脚本，演员在平板上观看 |

---

## ✨ 核心功能

### 多种文本导入
- 📋 剪贴板粘贴
- 📁 拖放 .txt / .md 文件
- 🌐 从 URL 加载（自动 CORS 代理回退）
- ⌨️ 手动输入编辑

### 文字实时调整
- 字号 20-120px（滑块 + 键盘 ±）
- 三种字体：无衬线 / 衬线 / 等宽
- 四档行距：紧凑 / 标准 / 宽松 / 极宽
- 左中右对齐
- 支持 **粗体** 和 *斜体*

### 速度控制
- 🎡 **物理引擎翻动选择器**：手指翻动 → 惯性滑行 → 自动吸附，类似 iOS 闹钟体验
- 速度范围 10-100，16 档位
- 键盘 ← → 跳档，鼠标滚轮也支持

### 双端协同（Server 模式）
- 笔记本管理端 `/admin` — 编辑脚本并推送
- 平板客户端 `/` — 纯显示 + 触控操作
- 内容实时同步，客户端自动拉取更新

### 全屏沉浸
- 全屏后 UI 自动隐藏（3 秒无操作）→ 触碰屏幕浮现
- 拖动回溯已滚动内容
- 单击暂停/继续
- 镜像翻转（适配物理提词器反射镜）
- 中心阅读引导线

---

## 🚀 一键使用

### 方式一：在线直接使用 🌐

👉 **[xxxcjyxxx.github.io/teleprompter-studio](https://xxxcjyxxx.github.io/teleprompter-studio/)**

点开即用，不需要安装任何东西。GitHub Pages 托管，全静态。

### 方式二：下载离线使用（单机版）

下载 `teleprompter.html`，直接拖进浏览器即可。纯离线，无网络也能跑。

### 方式三：内网服务端（双端版）

```bash
# 1. 确保有 Python 3（macOS / Linux 自带）
python3 --version

# 2. 启动服务
python3 prompter-server.py

# 3. 终端会打印两个链接：
#    📱 客户端 (平板):   http://192.168.x.x:8080/
#    ✏️  管理端 (编辑):   http://192.168.x.x:8080/admin
```

**自定义端口：**
```bash
python3 prompter-server.py 9090
```

> 零依赖，纯 Python 3 标准库。笔记本和平板连同一个 WiFi 就行。

---

## ⌨️ 快捷键

### 客户端（平板端）

| 键 | 功能 |
|----|------|
| `Space` | 播放 / 暂停 |
| `Esc` | 停止并回到开头 |
| `←` `→` | 速度跳一档 |
| `↑` `↓` | 字号 ±4px |
| `F` | 全屏切换 |
| `M` | 镜像翻转 |
| `1` `2` `3` | 没用上（留给未来主题切换） |

### 管理端

| 键 | 功能 |
|----|------|
| `Cmd+S` / `Ctrl+S` | 推送到客户端 |

---

## 📐 架构

```
单机版：
  teleprompter.html ─── 一个文件，所有 CSS/JS 内联，双击即用

双端版：
  ┌──────────────────────┐        ┌──────────────────────┐
  │  管理端 /admin        │  POST  │  客户端 /             │
  │  (笔记本 · 编辑推送)   │ ────→ │  (平板 · 显示触控)     │
  │                      │        │                      │
  │  编辑区 + 拖放 + URL  │        │  翻动选速度 + 拖动回溯  │
  │  Cmd+S 推送           │        │  全屏自动隐藏 UI       │
  └──────────┬───────────┘        └──────────┬───────────┘
             │                               │
             └───── prompter-server.py ──────┘
                     HTTP API + 内存状态
                     版本号轮询 (800ms)
```

**技术栈：**
- 服务端：Python 3 `http.server` + `socketserver`（零依赖）
- 客户端：原生 HTML/CSS/JS（零框架）
- 速度选择器：手写物理引擎（velocity tracking + momentum + snap）
- 同步：RESTful polling（版本号比对，800ms 间隔）

---

## 📚 灵感来源

本项目设计参考了以下优秀开源项目：

- **[jonkost/Prompt-Up-The-Jam](https://github.com/jonkost/Prompt-Up-The-Jam)** — 单文件 HTML 提词器，提供了极佳的 fade 边缘、引导线、镜像模式 UX 参考
- **[ImaginarySense/Imaginary-Teleprompter](https://github.com/ImaginarySense/Imaginary-Teleprompter)** — 老牌免费提词器软件，功能全面的 Electron 应用
- 速度选择器的物理引擎借鉴了 **BetterScroll / iScroll** 的 momentum 算法思路（velocity tracking + exponential decay + snap）

---

## 🛠 部署建议

### 长期使用（macOS/Linux）

```bash
# 后台运行
nohup python3 prompter-server.py > /tmp/prompter.log 2>&1 &

# 或者做成 systemd service (Linux)
# 或者 launchd (macOS)
```

### 公网访问（谨慎）

生产环境请在前面加 nginx 反向代理 + HTTPS。内网工具不建议直接暴露到公网。

### 离线使用

单机版 `teleprompter.html` 完全离线可用。双端版只需 Python 3 标准库，不联网也能在内网运行。

---

## 📄 License

MIT © 2025

---

<div align="center">

**翻动选速度 · 拖动可回溯 · 全屏自隐藏**

</div>
