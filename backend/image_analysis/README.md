# 简化版VLM图像分析器

## 📋 项目简介

这是一个专注于**工业图纸和技术文档**的VLM（视觉语言模型）图像分析工具。

**第一步实现**：加载图片 + VLM识别 + 根据用户问题回复

支持三种应用场景：
1. **CAD工程制造图纸解读** - 识别结构、尺寸、参数
2. **研发架构图理解** - 识别架构、流程图语义
3. **工业技术档案识别** - 识别工艺文件、设计版本

## 🚀 快速开始

### 安装依赖

```bash
pip install pillow aiohttp requests openai
```

### 基础使用

```python
import asyncio
from simple_vlm_analyzer import SimpleVLMAnalyzer, ImageType

async def main():
    # 1. 创建分析器
    analyzer = SimpleVLMAnalyzer()

    # 2. 分析图片
    result = await analyzer.analyze_image(
        image_source="/path/to/your/image.jpg",  # 本地路径或URL
        question="这张图纸的主要尺寸是多少？",      # 用户问题
        image_type=ImageType.CAD                 # 图像类型
    )

    # 3. 查看结果
    analyzer.print_result(result)

    # 或直接访问结果字段
    print(result.answer)          # 回答
    print(result.extracted_info)  # 提取的结构化信息
    print(result.time_cost)       # 耗时

asyncio.run(main())
```

## 📖 详细使用说明

### 1. 支持的图像类型

```python
from simple_vlm_analyzer import ImageType

# 三种图像类型
ImageType.CAD            # CAD工程制造图纸
ImageType.ARCHITECTURE   # 研发架构图/流程图
ImageType.TECHNICAL_DOC  # 工业技术档案/工艺文件
```

### 2. 图片加载方式

支持三种方式加载图片：

#### 方式1: 本地文件路径
```python
result = await analyzer.analyze_image(
    image_source="/home/user/cad_drawing.jpg",
    question="主要尺寸是多少？",
    image_type=ImageType.CAD
)
```

#### 方式2: HTTP/HTTPS URL
```python
result = await analyzer.analyze_image(
    image_source="https://example.com/diagram.png",
    question="系统架构是怎样的？",
    image_type=ImageType.ARCHITECTURE
)
```

#### 方式3: PIL Image对象
```python
from PIL import Image

img = Image.open("photo.jpg")
result = await analyzer.analyze_image(
    image_source=img,
    question="关键参数是什么？",
    image_type=ImageType.TECHNICAL_DOC
)
```

### 3. 自定义API配置

```python
# 使用自定义API
analyzer = SimpleVLMAnalyzer(
    model_url="https://your-api.com/v1",
    api_key="your-api-key",
    model_name="gpt-4o"
)

# 使用通义千问
analyzer = SimpleVLMAnalyzer(
    model_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key="your-qwen-key",
    model_name="qwen-vl-plus"
)
```

### 4. 便捷函数

```python
from simple_vlm_analyzer import (
    analyze_cad_drawing,
    analyze_architecture_diagram,
    analyze_technical_document
)

# 快速分析CAD图纸
result = await analyze_cad_drawing(
    image_source="cad.jpg",
    question="主要尺寸？"
)

# 快速分析架构图
result = await analyze_architecture_diagram(
    image_source="arch.png",
    question="系统架构？"
)

# 快速分析技术文档
result = await analyze_technical_document(
    image_source="doc.jpg",
    question="关键参数？"
)
```

## 🎯 应用场景示例

### 场景1: CAD工程图纸分析

```python
analyzer = SimpleVLMAnalyzer()

result = await analyzer.analyze_image(
    image_source="mechanical_drawing.jpg",
    question="这个零件的主要尺寸、公差要求和材料是什么？",
    image_type=ImageType.CAD
)

# 提取的信息包括：
# - drawing_title: 图纸名称
# - drawing_number: 图纸编号
# - main_dimensions: 主要尺寸
# - material: 材料
# - technical_requirements: 技术要求
# - views: 包含的视图
```

**适合的问题示例：**
- "这张图纸的主要尺寸是多少？"
- "图纸中标注的公差范围是什么？"
- "这个零件使用什么材料？"
- "图纸包含哪些视图？"
- "表面粗糙度要求是多少？"

### 场景2: 系统架构图分析

```python
result = await analyzer.analyze_image(
    image_source="system_architecture.png",
    question="这个系统分为几层？各层的主要组件有哪些？数据流向是怎样的？",
    image_type=ImageType.ARCHITECTURE
)

# 提取的信息包括：
# - diagram_type: 图表类型
# - main_components: 主要组件
# - layers: 系统层级
# - data_flow: 数据流向
# - key_technologies: 关键技术
```

**适合的问题示例：**
- "这个系统分为哪几层？"
- "各个模块之间是如何通信的？"
- "数据流向是怎样的？"
- "使用了哪些技术栈？"
- "这个流程的关键决策点在哪里？"

### 场景3: 工艺文件/技术档案分析

```python
result = await analyzer.analyze_image(
    image_source="process_card.jpg",
    question="这份工艺卡片的加工步骤和质量要求是什么？",
    image_type=ImageType.TECHNICAL_DOC
)

# 提取的信息包括：
# - document_type: 文档类型
# - document_number: 文档编号
# - version: 版本号
# - key_parameters: 关键参数
# - process_steps: 工艺步骤
# - inspection_items: 检验项目
```

**适合的问题示例：**
- "这份文档的版本号是多少？"
- "工艺流程包含哪些步骤？"
- "关键参数和数值是什么？"
- "表格中记录了哪些数据？"
- "检验标准是什么？"

## 📊 返回结果说明

### AnalysisResult 对象

```python
@dataclass
class AnalysisResult:
    image_type: str              # 图像类型
    question: str                # 用户问题
    answer: str                  # VLM的回答
    extracted_info: Dict         # 提取的结构化信息
    raw_response: str            # 原始响应
    token_usage: Dict[str, int]  # Token使用统计
    time_cost: float             # 耗时（秒）
```

### 访问结果

```python
result = await analyzer.analyze_image(...)

# 直接访问字段
print(result.answer)              # 获取回答
print(result.extracted_info)      # 获取结构化信息
print(result.time_cost)           # 获取耗时
print(result.token_usage)         # 获取Token统计

# 美化打印
analyzer.print_result(result)
```

## 🔧 高级功能

### 批量处理多张图片

```python
images = [
    {"path": "drawing1.jpg", "question": "主要尺寸？"},
    {"path": "drawing2.jpg", "question": "材料？"},
    {"path": "drawing3.jpg", "question": "公差？"}
]

results = []
for img in images:
    result = await analyzer.analyze_image(
        image_source=img["path"],
        question=img["question"],
        image_type=ImageType.CAD
    )
    results.append(result)
    await asyncio.sleep(1)  # 避免API限流
```

### 保存结果到文件

```python
import json

result = await analyzer.analyze_image(...)

# 保存为JSON
with open("result.json", "w", encoding="utf-8") as f:
    json.dump({
        "question": result.question,
        "answer": result.answer,
        "extracted_info": result.extracted_info,
        "time_cost": result.time_cost,
        "token_usage": result.token_usage
    }, f, ensure_ascii=False, indent=2)
```

## 📝 配置说明

### 环境变量配置（可选）

```python
import os

# 从环境变量读取配置
analyzer = SimpleVLMAnalyzer(
    model_url=os.getenv("VLM_API_URL", "https://aizex.top/v1"),
    api_key=os.getenv("VLM_API_KEY", "your-default-key"),
    model_name=os.getenv("VLM_MODEL_NAME", "gpt-4o")
)
```

### 支持的模型

- **OpenAI GPT系列**: gpt-4o, gpt-4-turbo, gpt-4-vision-preview
- **通义千问**: qwen-vl-plus, qwen-vl-max
- **Claude**: claude-3-opus, claude-3-sonnet
- **其他OpenAI兼容API**: 任何兼容OpenAI格式的多模态模型

## 🧪 运行测试

### 运行测试套件
```bash
python test_vlm_analyzer.py
```

### 运行示例脚本
```bash
python example_usage.py
```

## ⚠️ 注意事项

1. **API密钥安全**: 不要将API密钥硬编码到代码中，建议使用环境变量
2. **图片大小**: 大图片会自动压缩到2000px，减少Token消耗
3. **API限流**: 批量处理时建议添加延迟（如 `await asyncio.sleep(1)`）
4. **网络超时**: 默认超时300秒，可根据需要调整
5. **Token消耗**: 图片分析会消耗较多Token，请注意成本

## 🔍 故障排除

### 问题1: 文件不存在
```
FileNotFoundError: 图片文件不存在
```
**解决**: 检查图片路径是否正确，使用绝对路径

### 问题2: API调用失败
```
API调用失败: 401
```
**解决**: 检查API密钥是否正确，是否过期

### 问题3: JSON解析失败
```
JSON解析失败
```
**解决**: 模型返回格式可能不标准，会自动降级为纯文本处理

### 问题4: 网络超时
```
请求超时
```
**解决**: 检查网络连接，或增加超时时间

## 📄 项目结构

```
backend/image_analysis/
├── simple_vlm_analyzer.py   # 核心分析器代码
├── test_vlm_analyzer.py     # 测试脚本
├── example_usage.py         # 使用示例
└── README.md                # 本文档
```

## 🎓 设计思路

本工具的设计遵循以下原则：

1. **专注第一步**: 先实现基本的图像识别和问答功能，不涉及入库、检索
2. **场景化提示词**: 针对三种工业场景定制了专业的提示词模板
3. **灵活输入**: 支持本地文件、URL、PIL对象三种输入方式
4. **结构化输出**: VLM返回JSON格式的结构化信息，便于后续处理
5. **多模型支持**: 兼容OpenAI、通义千问、Claude等主流VLM
6. **易于扩展**: 后续可方便地添加向量入库、语义检索等功能

## 🚧 后续规划

- [ ] 添加图片OCR文本提取
- [ ] 支持多张图片联合分析
- [ ] 集成向量数据库（Milvus）
- [ ] 实现语义检索功能
- [ ] 添加图片缓存机制
- [ ] 支持流式输出

## 📞 联系方式

如有问题或建议，欢迎反馈！

---

**版本**: v1.0 - 第一步实现
**更新时间**: 2025-10-14
