# 室内平面图 VLM 分析 - 优化说明

## 📋 优化内容总结

### 1. 新增图像类型：`floor_plan`

在 [config.py:143](config.py#L143) 中添加了新的图像类型：

```python
IMAGE_TYPES = {
    ...
    "floor_plan": "室内平面布置图/建筑平面图",
    ...
}
```

### 2. 专门优化的提示词

在 [vlm_analyzer.py:138-273](core/vlm_analyzer.py#L138-L273) 中添加了专门针对室内平面图的详细提示词，包含以下核心功能：

#### ✅ 分析维度（6大类）

1. **房间/功能区识别**
   - 识别所有房间名称（客厅、卧室、厨房等）
   - 标注位置（左上、右下、中央等）
   - 识别特殊功能区（储藏室、玄关等）

2. **尺寸标注解析**
   - 提取所有尺寸数值
   - 推断单位并统一换算（mm/cm/m）
   - 计算房间面积
   - 标注整体外墙尺寸

3. **符号与标注识别**
   - 解释虚线、箭头、红点/红线等符号
   - 识别文字标注（编号、面积、备注）
   - 说明墙体类型和门窗位置

4. **家具布局识别**
   - 列出所有家具及位置
   - 标注家具尺寸
   - 判断空间利用率

5. **动线与空间连通性**
   - 标出主入口、次入口
   - 描述主要动线路径
   - 列出房间连通关系
   - 判断布局类型（开放式/分隔式）

6. **设计评估与建议**（可选）
   - 动线合理性
   - 采光/朝向
   - 空间优化建议

#### 📊 结构化输出格式

提示词要求 VLM 输出严格的 JSON 格式，包含：

```json
{
    "total_dimensions": {
        "length": 22.72,
        "width": 12.5,
        "unit": "m",
        "total_area": 284.0
    },
    "rooms": [
        {
            "name": "客厅",
            "position": "中央偏右",
            "dimensions": {
                "length": 5.79,
                "width": 4.2,
                "area": 24.3,
                "unit": "m"
            },
            "furniture": ["沙发", "茶几", "电视柜"],
            "connected_to": ["餐厅", "卧室1"],
            "windows": 2,
            "doors": 1
        }
    ],
    "annotations": [...],
    "symbols": [...],
    "circulation": {...},
    "design_notes": [...],
    "description": "整体描述"
}
```

---

## 🚀 使用方法

### 方式1：使用测试脚本（推荐）

```bash
cd /home/MuyuWorkSpace/01_TrafficProject/pc_multimodal_rag/backend/Information-Extraction/04_vlm_based/engineering_drawing_retrieval/examples

# 方式1: 使用默认路径
python test_floor_plan.py

# 方式2: 指定你的图片路径
python test_floor_plan.py /path/to/your/floor_plan.jpg
```

### 方式2：在代码中使用

```python
import asyncio
from core.vlm_analyzer import EngineeringDrawingAnalyzer

async def analyze_my_floor_plan():
    # 创建分析器
    analyzer = EngineeringDrawingAnalyzer()

    # 分析室内平面图
    result = await analyzer.analyze_image(
        image_path="/path/to/your/floor_plan.jpg",
        image_type="floor_plan"  # 指定类型为 floor_plan
    )

    # 获取结构化数据
    structured_data = result.structured_data

    # 获取文字描述
    description = result.description

    # 打印结果
    import json
    print(json.dumps(structured_data, ensure_ascii=False, indent=2))

    return result

# 运行
asyncio.run(analyze_my_floor_plan())
```

### 方式3：自动识别类型

```python
async def auto_analyze():
    analyzer = EngineeringDrawingAnalyzer()

    # 自动识别图像类型
    image_type = await analyzer.classify_image_type("/path/to/image.jpg")
    print(f"识别类型: {image_type}")

    # 使用识别的类型分析
    result = await analyzer.analyze_image("/path/to/image.jpg", image_type)

    return result
```

### 方式4：自定义提示词（针对特定需求）

```python
async def custom_analysis():
    analyzer = EngineeringDrawingAnalyzer()

    custom_prompt = """
    请只回答以下问题：
    1. 这张平面图有几个卧室？
    2. 客厅面积大约多少？
    3. 是否有独立卫生间？

    JSON 格式输出。
    """

    result = await analyzer.analyze_image(
        image_path="/path/to/floor_plan.jpg",
        image_type="floor_plan",
        custom_prompt=custom_prompt  # 使用自定义提示词
    )

    return result
```

---

## 🧪 测试准备

### 1. 准备测试图片

将你的 CAD 平面图（JPG/PNG 格式）放在以下位置：

```
examples/floor_plan_sample.jpg
```

或者修改测试脚本中的路径。

### 2. 检查配置

确保 [config.py](config.py) 中的 VLM API 配置正确：

```python
@dataclass
class VLMConfig:
    api_key: str = "your-api-key"
    base_url: str = "https://aizex.top/v1"
    model_name: str = "gpt-4o"  # 或其他支持视觉的模型
```

### 3. 运行测试

```bash
python test_floor_plan.py
```

预期输出：

```
✅ 找到图片: examples/floor_plan_sample.jpg
✅ 分析成功!

📊 结构化数据:
{
  "total_dimensions": {
    "length": 22.72,
    "width": 12.5,
    ...
  },
  "rooms": [...],
  ...
}

💾 结果已保存到: examples/test_floor_plan_result.json
```

---

## 📌 注意事项

### 提示词优化要点

1. **明确图像类型**
   - 开头就说明这是"室内平面布置图"，帮助模型建立正确上下文

2. **结构化输出**
   - 提供详细的 JSON Schema 示例
   - 模型更容易理解预期输出格式

3. **分类细化**
   - 把分析任务拆分为 6 大类
   - 每类都有明确的子任务

4. **示例驱动**
   - 提供具体数值示例（如 "22720mm = 22.72m"）
   - 帮助模型理解单位换算逻辑

5. **容错处理**
   - 告诉模型：如果标注不清，可以标注"不可读"或估算
   - 避免模型因为不确定而拒绝回答

### 模型选择建议

| 模型 | 优点 | 缺点 | 推荐场景 |
|------|------|------|----------|
| GPT-4o | 视觉理解强，输出质量高 | 成本较高 | 生产环境 |
| GPT-4o-mini | 成本低，速度快 | 细节识别较弱 | 快速原型/测试 |
| Claude 3 Opus | 理解细致，长文本能力强 | API 限制较多 | 复杂图纸分析 |
| Qwen-VL-Max | 中文优化好，成本低 | 英文技术术语较弱 | 中文标注图纸 |

### 常见问题

#### Q1: 模型无法识别尺寸标注？

**解决方案**：
- 确保图片分辨率足够（建议 ≥ 2000px）
- 在提示词中明确"请仔细识别所有数字标注"
- 可以预处理图片（增强对比度、锐化）

#### Q2: JSON 解析失败？

**解决方案**：
- 检查 [vlm_analyzer.py:256-262](core/vlm_analyzer.py#L256-L262) 的 JSON 提取逻辑
- 模型可能在 JSON 前后加了额外说明文字
- 可以在提示词末尾强调"只返回 JSON，不要其他文字"

#### Q3: 识别的图像类型不是 floor_plan？

**解决方案**：
- 手动指定 `image_type="floor_plan"`，不依赖自动识别
- 或优化 [vlm_analyzer.py:332-338](core/vlm_analyzer.py#L332-L338) 的分类提示词

#### Q4: 想要更简洁/更详细的输出？

**解决方案**：
- 使用 `custom_prompt` 参数自定义提示词
- 或直接修改 [vlm_analyzer.py:138-273](core/vlm_analyzer.py#L138-L273) 中的默认提示词

---

## 🎯 下一步优化方向

### 短期优化

1. **多模态融合**
   - 结合 OCR（PaddleOCR/Tesseract）提取文字
   - VLM 专注于布局和空间关系理解

2. **后处理优化**
   - 添加尺寸验证逻辑（如：总长 = 各段之和）
   - 自动修正单位错误

3. **批量处理**
   - 支持多张图纸对比分析
   - 输出差异报告

### 长期优化

1. **微调专用模型**
   - 收集建筑平面图数据集
   - 微调 VLM 提高准确率

2. **图纸知识库**
   - 建立建筑规范知识库
   - 在提示词中注入领域知识

3. **交互式分析**
   - 支持用户追问（如"客厅在哪儿？"）
   - 多轮对话逐步细化分析

---

## 📚 参考资料

- [CAD 图纸标注规范](https://www.example.com)
- [建筑制图标准 GB/T 50001](https://www.example.com)
- [VLM 提示词工程最佳实践](https://www.anthropic.com/prompt-engineering)

---

## 🤝 贡献

如果你有更好的提示词优化建议，欢迎提交 PR 或 Issue！

优化记录：
- 2025-01-XX: 初版 floor_plan 提示词
- 2025-01-XX: 添加家具布局识别
- 2025-01-XX: 增强动线分析能力
