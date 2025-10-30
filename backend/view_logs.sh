#!/bin/bash
# 查看服务日志

LOG_DIR="./logs"
LATEST_LOG=$(ls -t $LOG_DIR/rag_service_*.log 2>/dev/null | head -1)

if [ -z "$LATEST_LOG" ]; then
    echo "❌ 没有找到日志文件"
    exit 1
fi

echo "📄 查看最新日志文件: $LATEST_LOG"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 如果有参数，按参数执行
if [ "$1" == "tail" ]; then
    # 实时跟踪日志
    tail -f "$LATEST_LOG"
elif [ "$1" == "error" ]; then
    # 只显示错误日志
    grep "ERROR\|❌" "$LATEST_LOG"
elif [ "$1" == "request" ]; then
    # 只显示请求日志
    grep "📥\|📤\|🔍\|📤\|💬" "$LATEST_LOG"
else
    # 显示最后50行
    tail -50 "$LATEST_LOG"
fi
