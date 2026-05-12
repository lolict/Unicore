#!/bin/bash
# UniCore 一键推送到 GitHub

USERNAME=${1:-"lolict"}
REPO=${2:-"UniCore"}

echo "========================================"
echo " UniCore GitHub 推送工具"
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

# 推送
echo "🚀 推送到 GitHub..."
git push -u origin main

echo ""
echo "✅ 完成！"
echo ""
echo "仓库地址: https://github.com/$USERNAME/$REPO"
