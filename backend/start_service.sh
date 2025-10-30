#!/bin/bash
# 多模态 RAG 服务启动脚本

echo "🚀 启动多模态 RAG 服务..."
echo "使用 Conda 环境: multimodal_rag"
echo ""

# 使用 Conda 环境的 Python
/root/anaconda3/envs/multimodal_rag/bin/python main_service.py
