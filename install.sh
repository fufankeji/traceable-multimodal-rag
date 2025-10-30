#!/bin/bash

echo "========================================="
echo "安装所有依赖"
echo "========================================="

# 检查 uv
if ! command -v uv &> /dev/null; then
    echo "未检测到 uv，正在安装 uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
    if ! command -v uv &> /dev/null; then
        echo "uv 安装失败，请手动安装 uv"
        exit 1
    fi
fi

echo "1. 创建 Python 虚拟环境..."
# 使用 uv 创建虚拟环境
uv venv .venv --python 3.11
source .venv/bin/activate

echo "2. 安装后端依赖..."
cd ./backend
# 使用 uv 安装 Python 依赖
uv pip install -r requirements_service.txt

echo "3. 安装前端依赖..."
cd ../frontend
npm install

echo "========================================="
echo "安装完成！"
echo "使用 './start.sh' 启动服务"
echo "========================================"