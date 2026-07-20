# Changelog

所有值得注意的变更都会记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [1.3.0] - 2026-07-21

### 新增
- **智能首页**：自动检测访问方式，提供三种入口
  - ✏️ 编辑脚本 → 生成含内容的链接 + 二维码，平板扫码即用
  - 📱 直接打开提词器（默认示例脚本或用户内容）
  - 📋 粘贴脚本 → 一键进入提词模式
- **内容编码进 URL**：脚本通过 Base64 编码写入 `#c=...` 片段
  - 生成链接 → 平板扫码 → 自动解析并进入提词模式
  - 无需服务器，纯静态 Pages 即可实现「编辑-分享-提词」闭环
- **QR 码自动生成**：通过 qrserver.com API 实时生成
- **macOS 一键启动器** `start.command`：双击直接跑服务 + 自动打开浏览器
- **提词器客户端返回按钮**：可一键回到编辑页面

### 变更
- `index.html` 重构为「首页 + 编辑器 + 客户端」三合一
- 服务端 `/` 路由改为展示首页（客户端走 `/client`）
- `teleprompter.html` 同步为与 `index.html` 相同的新版本

### 移除
- 旧版独立提词器首页（空白页等待推送）

---

## [1.2.2] - 2026-07-18

### 文档
- 新增 `CHANGELOG.md`，完整记录所有版本变更历史
- README 顶部添加醒目的一键使用链接 badge

---

## [1.2.1] - 2026-07-18

### 新增
- 启用 GitHub Pages 部署：`https://xxxcjyxxx.github.io/teleprompter-studio/`
- 新增 `index.html`，点开即用，零门槛

### 文档
- README 新增「在线直接使用」入口，和 `digital-idle-calculator` 体验一致
- 补充一键使用、部署、在线体验的三种方式链接

---

## [1.2.0] - 2026-07-18

### 新增
- **物理引擎翻动式速度选择器**：替代 CSS scroll-snap
  - 手指翻动 → 速度追踪（velocity tracking）
  - 松手后惯性滑行 → 指数衰减摩擦（0.945）
  - 速度低于阈值后自动吸附到最近档位
  - 支持鼠标滚轮、方向键跳档
- **客户端文字调整**：字体切换（无衬线 / 衬线 / 等宽）、行距切换（紧凑 / 标准 / 宽松 / 极宽）
- **管理端增强导入**：拖放区域、从剪贴板粘贴、从 URL 加载（带 CORS 代理回退）

### 变更
- 速度选择器 UI 重设计：金色选中框 + 高亮放大 + 两侧渐变遮罩
- 管理端支持 .html / .htm / .csv / .json 等多格式文件导入

### 移除
- CSS `scroll-snap-type` 速度选择器（无动量惯性，体验不佳）

---

## [1.1.0] - 2026-07-18

### 新增
- **双端架构 `prompter-server.py`**：Python 3 零依赖内网服务端
  - `/` → 平板客户端（全屏沉浸、触控操作）
  - `/admin` → 笔记本管理端（编辑脚本、推送内容）
  - `/api/content` + `/api/version` → 版本号轮询同步
- **CSS scroll-snap 速度选择器**（第一版，后续在 v1.2.0 被物理引擎替代）
- 全屏自动隐藏 UI + 触碰浮现
- 触摸拖动回溯已滚动内容
- 单击暂停 / 继续
- 镜像翻转模式
- 阅读引导线
- 连接中断提示 + 自动重连

### 变更
- 将原 `teleprompter.html` 定位为单机版，`prompter-server.py` 为双端版

---

## [1.0.0] - 2026-07-18

### 新增
- **`teleprompter.html` 单机版**，零依赖，浏览器直接打开
- 四种文本导入方式：粘贴、文件上传、URL 加载、拖放
- 文字调整：字号 20-120px、字体选择、行距、对齐、**粗体** / *斜体*
- 速度滑块控制（5-100）
- `requestAnimationFrame` 平滑滚动引擎
- 三种主题：暗色、亮色、绿色护眼
- 全屏模式 + 键盘快捷键
- localStorage 自动保存 / 恢复
- 进度百分比 + 字数统计

### 参考来源
- 设计灵感来自 [Prompt-Up-The-Jam](https://github.com/jonkost/Prompt-Up-The-Jam)（单文件提词器）
- 功能参考 [Imaginary-Teleprompter](https://github.com/ImaginarySense/Imaginary-Teleprompter)（桌面提词器软件）
- 速度选择器物理引擎借鉴 BetterScroll / iScroll 的 momentum 算法思路

---

## [Unreleased]

### 计划中
- [ ] SSE / WebSocket 实时推送替代轮询
- [ ] 多客户端同步管理（同时控制多台平板）
- [ ] 语音跟随模式（根据语速自动调速）
- [ ] PWA 支持（安装到桌面，离线可用）
- [ ] 暗色 / 亮色 / 绿色 三主题在客户端可用（快捷键 1/2/3）
- [ ] Windows `start.bat` 一键启动器

---

[1.3.0]: https://github.com/XxxCJYxxX/teleprompter-studio/compare/v1.2.2...HEAD
[1.2.2]: https://github.com/XxxCJYxxX/teleprompter-studio/releases/tag/v1.2.2
[1.2.1]: https://github.com/XxxCJYxxX/teleprompter-studio/releases/tag/v1.2.1
[1.2.0]: https://github.com/XxxCJYxxX/teleprompter-studio/releases/tag/v1.2.0
[1.1.0]: https://github.com/XxxCJYxxX/teleprompter-studio/releases/tag/v1.1.0
[1.0.0]: https://github.com/XxxCJYxxX/teleprompter-studio/releases/tag/v1.0.0
