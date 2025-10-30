#!/bin/bash

# 检查 uv
if ! command -v uv &> /dev/null; then
    echo "未检测到 uv，请先运行 './install.sh' 进行安装"
    exit 1
fi

# 检查虚拟环境是否存在
if [ ! -d ".venv" ]; then
    echo "错误: 未找到虚拟环境 '.venv'"
    echo "请先运行 './install.sh' 进行安装"
    exit 1
fi

echo "1. 激活虚拟环境..."
source .venv/bin/activate

echo "2. 启动后端服务..."
cd ./backend
if [ -f "main_service.py" ]; then
    echo "后端服务启动中... (端口: 8000)"
    nohup uv run python main_service.py > backend.log 2>&1 &
    BACKEND_PID=$!
    echo "后端服务PID: $BACKEND_PID"
    echo "后端日志文件: backend/backend.log"
else
    echo "错误: 未找到 main_service.py 文件"
    exit 1
fi

# 等待后端启动
sleep 3

echo "3. 启动前端服务..."
cd ../frontend
if [ -f "package.json" ]; then
    echo "前端服务启动中..."
    nohup npm run dev > frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo "前端服务PID: $FRONTEND_PID"
    echo "前端日志文件: frontend/frontend.log"
else
    echo "错误: 未找到 package.json 文件"
    kill $BACKEND_PID
    exit 1
fi

echo "========================================="
echo "服务启动完成！"
echo "后端服务: http://localhost:8000"
echo "前端服务: 请查看前端日志获取URL"
echo "========================================"

