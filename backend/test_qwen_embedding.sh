#!/bin/bash
# 测试通义千问 Embedding

echo "======================================"
echo "🧪 测试通义千问 Embedding"
echo "======================================"

# 检查环境变量
if [ -z "$DASHSCOPE_API_KEY" ]; then
    echo "⚠️  未设置 DASHSCOPE_API_KEY 环境变量"
    echo "请先设置: export DASHSCOPE_API_KEY=sk-your-key"
    exit 1
fi

echo "✓ 找到 DASHSCOPE_API_KEY"
echo ""

# 运行测试
python3 -c "
import os
from qwen_embeddings import QwenEmbeddings

print('🔧 初始化 Qwen Embeddings...')
embeddings = QwenEmbeddings(
    api_key=os.getenv('DASHSCOPE_API_KEY'),
    model='text-embedding-v4',
    dimensions=1024
)
print('✓ 初始化成功\n')

# 测试单个文本
print('📝 测试1: 单个文本向量化')
text = '衣服的质量杠杠的，很漂亮，不枉我等了这么久啊'
vector = embeddings.embed_query(text)
print(f'  文本: {text}')
print(f'  向量维度: {len(vector)}')
print(f'  向量前5维: {vector[:5]}')
print('  ✓ 测试通过\n')

# 测试批量文本
print('📝 测试2: 批量文本向量化')
texts = [
    '这是一个测试文本',
    '电机支架的孔径是42mm',
    '架构图显示了系统的数据流向'
]
vectors = embeddings.embed_documents(texts)
print(f'  文本数量: {len(texts)}')
print(f'  生成向量数: {len(vectors)}')
print(f'  每个向量维度: {len(vectors[0])}')
print('  ✓ 测试通过\n')

print('='*40)
print('✅ 所有测试通过！Qwen Embedding 工作正常')
print('='*40)
"
