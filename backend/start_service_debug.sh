#!/bin/bash

echo "🚀 启动多模态 RAG 服务（调试模式）..."

# 激活 Conda 环境
source ~/anaconda3/etc/profile.d/conda.sh
conda activate multimodal_rag

echo "使用 Conda 环境: $(conda info --envs | grep '*' | awk '{print $1}')"
echo ""

# 切换到后端目录
cd "$(dirname "$0")"

# 设置Python无缓冲输出
export PYTHONUNBUFFERED=1

# 加载环境变量
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# 启动服务
python -u main_service.py
