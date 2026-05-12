#!/bin/bash
# UniCore 一键推送到 GitHub
# 使用方法: ./push_to_github.sh <你的GitHub用户名> [仓库名]

USERNAME=${1:-"your-username"}
REPO=${2:-"UniCore"}

echo "========================================"
echo "UniCore GitHub 推送工具"
echo "========================================"
echo ""
echo "目标仓库: $USERNAME/$REPO"
echo ""

# 检查是否已登录
if ! gh auth status &> /dev/null; then
    echo "❌ 尚未登录 GitHub"
    echo ""
    echo "请先执行以下命令登录："
    echo ""
    echo "  gh auth login"
    echo ""
    echo "登录后重新运行此脚本"
    exit 1
fi

# 创建远程仓库（如果不存在）
echo "📦 创建 GitHub 仓库..."
gh repo create $REPO --public --source=. --remote=origin --push 2>/dev/null || {
    echo "仓库可能已存在，尝试推送..."
    git remote add origin https://github.com/$USERNAME/$REPO.git 2>/dev/null
}

# 提交代码
echo "📝 提交代码..."
git commit -m "Initial commit: UniCore Universal Platform

- UniISA: 自主统一指令集架构
- Universal VM: 通用虚拟机
- Binary Translator: 支持 x86/ARM/RISC-V/MIPS
- 多语言协作: Zig + Rust + Go + Python
- 跨平台支持: Web/Android/ESP32"

# 推送
echo "🚀 推送到 GitHub..."
git push -u origin master || git push -u origin main

echo ""
echo "✅ 完成！"
echo ""
echo "仓库地址: https://github.com/$USERNAME/$REPO"
