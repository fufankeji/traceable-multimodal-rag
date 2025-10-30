# 系统架构设计文档

## 1. 整体架构

### 1.1 分层架构

```
┌─────────────────────────────────────────────────────────────┐
│                    应用层 (Application)                      │
│  examples/                                                   │
│  - 01_index_drawings.py   (索引构建)                         │
│  - 02_search_drawings.py  (检索查询)                         │
│  - 03_quickstart.py       (快速开始)                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   检索层 (Retrieval)                         │
│  retrievers/                                                │
│  - HybridRetriever        (混合检索器)                       │
│  - Reranker              (重排序器)                          │
│  - Filter                (过滤器)                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    核心层 (Core)                             │
│  core/                                                       │
│  - VLM Analyzer          (图像语义理解)                      │
│  - Image Preprocessor    (图像预处理)                        │
│  - Embedding Manager     (向量化管理)                        │
│  - Vector Store          (向量存储)                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   基础设施层 (Infrastructure)                 │
│  - VLM API (GPT-4V / Claude-3.5 / Qwen-VL)                  │
│  - Vector DB (Milvus / Qdrant / Chroma)                     │
│  - OCR Engine (PaddleOCR)                                    │
│  - Image Processing (Pillow / OpenCV)                        │
└─────────────────────────────────────────────────────────────┘
```

## 2. 核心组件设计

### 2.1 VLM分析器 (EngineeringDrawingAnalyzer)

**职责:**
- 调用多模态大模型理解图像语义
- 针对不同图像类型使用专用prompt
- 自动识别图像类型
- 批量异步处理

**关键特性:**
```python
# 1. 类型化Prompt
get_prompt_by_type(image_type) -> str
  - engineering_drawing: 提取零件信息、尺寸、工艺
  - cad_drawing: 提取组件、装配关系
  - architecture_diagram: 提取组件、连接、技术栈
  - flowchart: 提取节点、流程、分支

# 2. 自动分类
classify_image_type(image_path) -> str
  返回: engineering_drawing | cad_drawing | architecture_diagram | ...

# 3. 批量处理（高性能）
analyze_batch(image_paths, max_concurrent=3)
  使用asyncio.Semaphore控制并发
  避免API限流
```

**性能优化:**
- 使用`langchain-openai`的异步API
- 并发控制：默认3个并发请求
- 自动重试机制
- Base64图像压缩（max_size=2000）

### 2.2 图像预处理器 (ImagePreprocessor)

**职责:**
- 图像质量检测
- OCR文本提取（小字说明）
- 图像增强（对比度、清晰度）
- 大图分割

**OCR增强:**
```python
# 使用PaddleOCR提取小字标注
extract_text_ocr(image_path) -> List[Dict]
  返回: [{text, bbox, confidence}]

# 适用场景：
# - 图纸上的尺寸标注
# - 技术参数说明
# - 零件编号
# - 材料标识
```

**质量检测:**
```python
detect_image_quality(image_path) -> Dict
  返回:
  {
    "resolution": (width, height),
    "is_high_quality": bool,
    "blur_score": float,      # Laplacian方差
    "brightness": float       # 平均亮度
  }
```

### 2.3 向量化管理器 (EmbeddingManager)

**职责:**
- 文本向量化（OpenAI Embedding API）
- 图像向量化（CLIP - 可选）
- 相似度计算

**双模态Embedding:**
```python
# 文本向量化
embed_text(text: str) -> List[float]
  模型: text-embedding-3-large (3072维)
  用途: VLM生成的描述、OCR文本

# 图像向量化（可选）
embed_image(image_path: str) -> List[float]
  模型: CLIP-ViT-Large (512维)
  用途: 视觉特征提取，支持以图搜图
```

### 2.4 向量存储 (EngineeringDrawingVectorStore)

**职责:**
- 封装向量数据库操作
- 支持多种向量数据库
- 文本和图像混合检索

**支持的数据库:**
- **Milvus** (推荐): 性能最好，适合大规模
- **Qdrant**: 功能丰富，部署简单
- **Chroma**: 轻量级，适合小规模

**数据结构:**
```python
Document:
  page_content: str         # VLM生成的描述
  metadata: {
    image_path: str         # 图像路径
    image_type: str         # 图像类型
    structured_data: dict   # VLM提取的结构化数据
    ocr_text: str          # OCR提取的文本
    image_vector: str      # 图像向量（JSON）
    quality: dict          # 图像质量信息
    page_number: int       # 页码
    source_pdf: str        # 来源PDF
  }
```

### 2.5 混合检索器 (HybridRetriever)

**职责:**
- 多策略检索
- 结果过滤和重排序
- 评分融合

**检索策略:**
```python
# 1. 纯文本检索
search(query: str, top_k=10)
  基于: VLM描述 + OCR文本
  算法: 余弦相似度

# 2. 图像检索（待实现）
search_by_example(image_path: str)
  基于: CLIP图像向量
  算法: L2距离/余弦相似度

# 3. 混合检索
search_hybrid(text_query, image_query)
  融合公式: score = α·text_score + β·image_score
  默认权重: α=0.6, β=0.4
```

**过滤条件:**
- `image_type`: 按图像类型过滤
- `min_score`: 最低相似度阈值
- 自定义元数据过滤

## 3. 数据流程

### 3.1 索引构建流程

```
PDF文档
  ↓
PyMuPDF提取页面为图像
  ↓
图像预处理 (去噪、增强)
  ↓
质量检测 (过滤低质量图像)
  ↓
OCR提取 (小字标注)
  ↓
VLM分析 (并发)
  ├─ 自动分类
  ├─ 语义理解
  └─ 结构化提取
  ↓
文本向量化
  ↓
存入向量数据库
```

### 3.2 检索流程

```
用户查询 (自然语言)
  ↓
文本向量化
  ↓
向量检索 (top_k × 2)
  ↓
过滤 (类型、分数)
  ↓
重排序 (可选)
  ↓
返回结果 (top_k)
```

## 4. 性能优化策略

### 4.1 索引构建优化

1. **异步并发**
   - 使用`asyncio.Semaphore`控制并发
   - 默认3个VLM并发请求
   - 避免触发API限流

2. **批量向量化**
   - `embed_documents`批量接口
   - 减少网络往返次数

3. **质量预过滤**
   - 跳过低质量图像
   - 减少无效VLM调用

4. **缓存机制**（待实现）
   - Redis缓存VLM结果
   - 避免重复分析

### 4.2 检索优化

1. **向量索引**
   - Milvus IVF_FLAT索引
   - 适合百万级数据

2. **多级检索**
   - 第一级：向量检索（快速）
   - 第二级：重排序（精确）

3. **结果缓存**
   - 热门查询缓存
   - TTL = 24小时

## 5. 扩展性设计

### 5.1 支持新的图像类型

```python
# 1. 在 config.py 添加类型
IMAGE_TYPES["circuit_diagram"] = "电路图"

# 2. 在 prompts/ 目录添加专用prompt
# prompts/circuit_diagram.py

# 3. 在 vlm_analyzer.py 添加prompt模板
def _get_prompt_by_type(self, image_type):
    prompts = {
        ...
        "circuit_diagram": "你的电路图分析prompt"
    }
```

### 5.2 切换VLM模型

```python
# config.py
class VLMConfig:
    # GPT-4V
    model_name = "gpt-4o"

    # 或 Claude-3.5-Sonnet
    # model_name = "claude-3-5-sonnet-20241022"
    # base_url = "https://api.anthropic.com"

    # 或 通义千问
    # model_name = "qwen-vl-max"
    # base_url = "https://dashscope.aliyuncs.com"
```

### 5.3 切换向量数据库

```python
# config.py
class VectorStoreConfig:
    # Milvus
    db_type = "milvus"

    # 或 Qdrant
    # db_type = "qdrant"

    # 或 Chroma
    # db_type = "chroma"
```

## 6. 部署架构

### 6.1 单机部署

```yaml
# docker-compose.yml
services:
  milvus:
    image: milvusdb/milvus:v2.3.0
    ports:
      - "19530:19530"

  app:
    build: .
    depends_on:
      - milvus
    environment:
      - VLM_API_KEY=xxx
      - MILVUS_HOST=milvus
```

### 6.2 分布式部署

```
┌─────────────┐
│   Nginx     │ 负载均衡
└─────┬───────┘
      │
  ┌───┴────┬────────┬────────┐
  │        │        │        │
┌─▼──┐ ┌──▼─┐ ┌───▼┐ ┌───▼─┐
│App1│ │App2│ │App3│ │App4│  应用集群
└─┬──┘ └──┬─┘ └───┬┘ └───┬─┘
  │       │       │      │
  └───────┴───────┴──────┘
          │
  ┌───────▼────────┐
  │  Milvus Cluster│  分布式向量库
  └────────────────┘
```

## 7. 监控和日志

### 7.1 关键指标

- **性能指标**
  - VLM调用延迟 (P50, P95, P99)
  - 向量检索延迟
  - 索引构建速度 (页/秒)

- **质量指标**
  - 图像分类准确率
  - 检索相关性 (MRR, NDCG)

- **系统指标**
  - API成功率
  - 向量库容量
  - 缓存命中率

### 7.2 日志规范

```python
# 使用结构化日志
logger.info(
    "vlm_analysis_complete",
    image_path=image_path,
    image_type=result.image_type,
    duration_ms=duration,
    token_usage=usage
)
```

## 8. 安全考虑

1. **API密钥管理**
   - 使用环境变量
   - 不提交到代码仓库
   - 定期轮换

2. **输入验证**
   - 图像格式检查
   - 文件大小限制
   - 路径遍历防护

3. **访问控制**
   - 向量库访问认证
   - API限流
   - 用户权限管理

## 9. 成本估算

### 9.1 VLM API成本

以GPT-4V为例：
- 输入：$0.01 / 1K tokens
- 输出：$0.03 / 1K tokens
- 平均每张图：~2000 tokens
- **成本：约 $0.05 / 图**

### 9.2 存储成本

- 向量维度：1536 (text-embedding-3-small)
- 每条记录：~6KB (向量 + 元数据)
- **10万张图：约 600MB**

### 9.3 计算成本

- Milvus：4核8G可支持10万级
- 应用服务：2核4G × 3 = 12G
- **月成本：约 $100 (云服务)**

## 10. 后续优化方向

1. **性能优化**
   - 实现图像向量检索
   - 添加重排序模型
   - 引入缓存层

2. **功能扩展**
   - 版本对比功能
   - 批注和标记
   - 3D CAD支持

3. **用户体验**
   - Web UI界面
   - 实时预览
   - 导出报告

4. **模型优化**
   - Fine-tune专用模型
   - 本地部署VLM
   - 量化加速
