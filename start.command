#!/bin/bash
# 提词器 · 一键启动 (macOS)
# 双击此文件即可启动内网服务端，自动打开管理页面

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "🎬  提词器 · 启动中…"
echo ""

python3 prompter-server.py

echo ""
echo "服务已停止。按任意键关闭此窗口。"
read -n 1
