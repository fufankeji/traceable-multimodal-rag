# 快速开始指南

5分钟搭建工程图纸语义检索系统

## 前置要求

- Python 3.8+
- Docker (用于Milvus)
- VLM API密钥 (GPT-4V / Claude-3.5 / Qwen-VL)

## 步骤1: 安装依赖

```bash
# 进入项目目录
cd engineering_drawing_retrieval

# 安装Python依赖
pip install -r requirements.txt
```

## 步骤2: 启动向量数据库

### 方式1: 使用Milvus (推荐)

```bash
# 下载docker-compose.yml
wget https://github.com/milvus-io/milvus/releases/download/v2.3.0/milvus-standalone-docker-compose.yml -O docker-compose.yml

# 启动Milvus
docker-compose up -d

# 检查状态
docker-compose ps
```

### 方式2: 使用Chroma (轻量级，无需Docker)

```python
# 修改 config.py
class VectorStoreConfig:
    db_type = "chroma"  # 改为chroma
```

## 步骤3: 配置API密钥

```python
# 编辑 config.py
class VLMConfig:
    api_key = "你的API密钥"
    base_url = "https://aizex.top/v1"  # 或其他endpoint
    model_name = "gpt-4o"

class EmbeddingConfig:
    text_api_key = "你的API密钥"
    text_base_url = "https://aizex.top/v1"
```

**或使用环境变量:**

```bash
export OPENAI_API_KEY="你的API密钥"
export OPENAI_BASE_URL="https://aizex.top/v1"
```

## 步骤4: 测试组件

```bash
# 运行组件测试
python examples/03_quickstart.py --test-only
```

期望输出：
```
==================================================
组件测试
==================================================

1. 测试VLM分析器...
   ✓ VLM分析器初始化成功

2. 测试向量存储...
   ✓ 向量存储初始化成功

3. 测试检索器...
   ✓ 检索器初始化成功

4. 测试向量库连接...
   ✓ 向量库连接成功: {'num_entities': 0, 'collection_name': 'engineering_drawings'}

==================================================
✓ 所有组件测试通过!
==================================================
```

## 步骤5: 索引你的第一个文档

### 5.1 准备文档

```bash
# 将你的PDF放到指定位置
cp your_document.pdf data/
```

### 5.2 修改路径并运行

```python
# 编辑 examples/01_index_drawings.py
pdf_path = "data/your_document.pdf"  # 修改为你的路径

# 运行索引
python examples/01_index_drawings.py
```

### 5.3 索引过程示例

```
开始处理PDF: your_document.pdf
============================================================
总页数: 50

处理第 1/50 页...
  图像质量: (1654, 2339), 清晰度: 856.3
  OCR提取: 342 字符
  图像类型: engineering_drawing
  ✓ VLM分析完成
  描述摘要: 这是一张轴承零件的工程制造图纸，包含主视图和剖视图。零件编号为ZC-2023-01...
  ✓ 已索引 (ID: a3b2c1d4...)

处理第 2/50 页...
...

============================================================
索引完成!
  成功: 45 页
  失败: 5 页
  总计: 50 页

向量库统计: {'num_entities': 45, 'collection_name': 'engineering_drawings'}
```

## 步骤6: 开始检索

### 6.1 交互式检索

```bash
python examples/02_search_drawings.py
```

### 6.2 检索示例

```
============================================================
示例6: 交互式检索
============================================================

可用的图像类型:
  - engineering_drawing: 工程制造图纸
  - cad_drawing: CAD技术图纸
  - architecture_diagram: 系统架构图
  - flowchart: 流程图
  - technical_document: 技术文档图片
  - circuit_diagram: 电路图
  - mechanical_drawing: 机械设计图

输入查询（输入'exit'退出）:

> 查找所有轴承相关的图纸

找到 5 条结果:

  [1] page_15.png
      相似度: 0.892
      类型: engineering_drawing
      这是一张深沟球轴承的工程制造图纸，包含零件的主视图、剖视图和详细尺寸标注...

  [2] page_23.png
      相似度: 0.875
      类型: cad_drawing
      轴承座的CAD装配图，展示了轴承与座体的配合关系...

  [3] page_41.png
      相似度: 0.854
      类型: engineering_drawing
      滚动轴承的技术要求说明页，包含材料、热处理、精度等级等信息...

> 找出包含尺寸公差的CAD图

找到 3 条结果:
...
```

## 步骤7: 在代码中使用

### 7.1 基础用法

```python
import asyncio
from retrievers.hybrid_retriever import HybridRetriever

async def search_drawings():
    # 初始化检索器
    retriever = HybridRetriever()

    # 执行检索
    results = await retriever.search(
        query="查找冷却系统相关的设计图",
        top_k=10,
        image_type="cad_drawing",  # 可选：过滤类型
        min_score=0.7              # 可选：最小相似度
    )

    # 处理结果
    for result in results:
        print(f"图纸: {result.image_path}")
        print(f"相似度: {result.score}")
        print(f"描述: {result.description}")
        print("-" * 60)

# 运行
asyncio.run(search_drawings())
```

### 7.2 高级用法

```python
from core.vlm_analyzer import EngineeringDrawingAnalyzer
from core.vector_store import EngineeringDrawingVectorStore

async def advanced_usage():
    # 1. 单独使用VLM分析器
    analyzer = EngineeringDrawingAnalyzer()
    result = await analyzer.analyze_image(
        "path/to/drawing.png",
        image_type="engineering_drawing"
    )
    print(f"分析结果: {result.to_dict()}")

    # 2. 批量分析
    results = await analyzer.analyze_batch(
        image_paths=["img1.png", "img2.png", "img3.png"],
        max_concurrent=3
    )

    # 3. 直接操作向量库
    vector_store = EngineeringDrawingVectorStore()
    doc_id = await vector_store.add_drawing(
        image_path="drawing.png",
        description="零件描述",
        metadata={"type": "engineering_drawing"}
    )

asyncio.run(advanced_usage())
```

## 常见问题

### Q1: Milvus连接失败

**问题：**
```
⚠ Milvus初始化失败: [Errno 111] Connection refused
```

**解决：**
```bash
# 检查Milvus是否运行
docker-compose ps

# 如果未运行，启动它
docker-compose up -d

# 等待30秒让Milvus完全启动
sleep 30
```

### Q2: OCR功能不可用

**问题：**
```
⚠ PaddleOCR未安装，OCR功能将被禁用
```

**解决：**
```bash
# 安装PaddleOCR
pip install paddleocr paddlepaddle

# 首次运行会下载模型，需要等待
```

### Q3: VLM API调用失败

**问题：**
```
VLM分析失败: 401 Unauthorized
```

**解决：**
- 检查API密钥是否正确
- 确认API额度充足
- 检查网络连接

### Q4: 内存不足

**问题：**
大量图像处理时内存溢出

**解决：**
```python
# 减少并发数
class VLMConfig:
    max_concurrent = 2  # 降低到2

# 或分批处理
for i in range(0, len(images), 10):
    batch = images[i:i+10]
    await indexer.index_images(batch)
```

### Q5: 检索结果不准确

**优化建议：**

1. **增加索引数据量**
   - 至少索引50+张图纸
   - 数据越多，效果越好

2. **调整相似度阈值**
   ```python
   results = await retriever.search(
       query="...",
       min_score=0.8  # 提高阈值
   )
   ```

3. **使用更好的Embedding模型**
   ```python
   class EmbeddingConfig:
       text_model = "text-embedding-3-large"  # 3072维
   ```

4. **优化查询描述**
   - ❌ "图纸"
   - ✓ "查找包含齿轮传动系统的机械设计图纸，需要有尺寸标注"

## 性能基准

**测试环境：**
- CPU: Intel i7-10700 (8核)
- 内存: 32GB
- GPU: 无
- VLM: GPT-4V

**性能数据：**
- 单张图片VLM分析: 2-5秒
- 并发3的批量处理: 10张图/分钟
- 向量检索延迟: <100ms
- 索引100页PDF: ~20分钟

## 下一步

1. **阅读架构文档**
   - [ARCHITECTURE.md](ARCHITECTURE.md) - 深入了解系统设计

2. **查看完整示例**
   - [examples/01_index_drawings.py](examples/01_index_drawings.py)
   - [examples/02_search_drawings.py](examples/02_search_drawings.py)

3. **定制化开发**
   - 添加新的图像类型支持
   - 实现图像检索功能
   - 集成到你的应用

4. **生产部署**
   - 使用Docker部署
   - 配置负载均衡
   - 添加监控和日志

## 获取帮助

- 查看 [README.md](README.md) 了解更多功能
- 提交 Issue 报告问题
- 参考 [LangChain文档](https://python.langchain.com/)

---

祝你使用愉快！🚀
