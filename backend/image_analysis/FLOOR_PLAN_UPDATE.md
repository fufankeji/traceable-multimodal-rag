# 室内平面图 VLM 分析 - 提示词优化更新

## 📋 更新内容

### 1. 新增图像类型：`ImageType.FLOOR_PLAN`

在 [simple_vlm_analyzer.py:45](simple_vlm_analyzer.py#L45) 添加了专门的室内平面图类型：

```python
class ImageType:
    CAD = "cad"  # CAD工程制造图纸
    FLOOR_PLAN = "floor_plan"  # 室内平面布置图/建筑平面图 ← 新增
    ARCHITECTURE = "architecture"  # 研发架构图/流程图
    TECHNICAL_DOC = "technical_doc"  # 工业技术档案/工艺文件
```

---

### 2. 专门优化的提示词（87-178行）

针对室内平面图场景，设计了包含 **6 大分析维度** 的详细提示词：

#### ✅ 分析维度

1. **房间/功能区识别**
   - 识别所有房间名称（客厅、卧室、厨房等）
   - 标注位置（左上/右下/中央）
   - 识别特殊功能区

2. **尺寸与面积**
   - 提取尺寸标注
   - 推断单位（mm/m）并换算
   - 计算房间面积

3. **符号与标注**
   - 解释符号（虚线、箭头、红点等）
   - 识别文字标注
   - 说明门窗位置

4. **家具布局**
   - 列出所有家具
   - 判断空间利用率
   - 识别家具尺寸

5. **动线与连通性**
   - 标出入口位置
   - 描述动线路径
   - 列出房间连通关系

6. **设计评估**
   - 动线合理性
   - 采光/朝向
   - 空间优化建议

#### 🎯 核心优化点

**针对用户问题的精准回答**：

```
**注意事项：**
- 优先回答用户的具体问题，不要罗列所有信息
- 如果用户问"有几个卧室"，就重点回答卧室数量和位置
- 如果用户问"客厅面积"，就重点回答客厅的尺寸和面积
- 保持答案简洁、针对性强
```

这是根据你提供的场景列表优化的关键点！

---

### 3. 便捷函数（707-716行）

新增快捷调用函数：

```python
async def analyze_floor_plan(
    image_source: Union[str, Path, Image.Image],
    question: str,
    model_url: str = DEFAULT_MODEL_URL,
    api_key: str = DEFAULT_API_KEY,
    model_name: str = DEFAULT_MODEL_NAME
) -> AnalysisResult:
    """分析室内平面布置图/建筑平面图"""
    analyzer = SimpleVLMAnalyzer(model_url, api_key, model_name)
    return await analyzer.analyze_image(image_source, question, ImageType.FLOOR_PLAN)
```

---

## 🚀 使用方法

### 方式 1：使用便捷函数（推荐）

```python
import asyncio
from simple_vlm_analyzer import analyze_floor_plan

async def main():
    result = await analyze_floor_plan(
        image_source="floor_plan.jpg",
        question="这张平面图有几个卧室？客厅面积多少？"
    )

    print(f"回答: {result.answer}")
    print(f"房间列表: {result.extracted_info.get('rooms')}")

asyncio.run(main())
```

### 方式 2：使用分析器类

```python
from simple_vlm_analyzer import SimpleVLMAnalyzer, ImageType

async def main():
    analyzer = SimpleVLMAnalyzer()

    result = await analyzer.analyze_image(
        image_source="floor_plan.jpg",
        question="动线设计合理吗？",
        image_type=ImageType.FLOOR_PLAN
    )

    analyzer.print_result(result)

asyncio.run(main())
```

---

## 💡 支持的问题类型（根据你提供的场景）

### 一、结构/布局理解类

#### 1. 房间/功能识别
```python
questions = [
    "请列出图中所有房间及其功能。",
    "这张图中有几个卧室？它们的位置在哪里？",
    "哪一区是起居区？哪一区是餐饮区？"
]
```

#### 2. 尺寸/长度/面积估算
```python
questions = [
    "请标出每个房间的长、宽尺寸。",
    "客厅的面积是多少？",
    "从主入口到次入口的直线距离大约是多少？"
]
```

#### 3. 标注/注释解析
```python
questions = [
    "图中标注 '579' 对应什么？是房间编号或面积吗？",
    "右上部分文字 '茶室' 是哪个房间？它在哪儿？",
    "红点与虚线路径表示什么？"
]
```

#### 4. 交通/动线分析
```python
questions = [
    "请指出主要动线（红线）所经过的房间顺序。",
    "从主入口到卧室的推荐路线是什么？",
    "哪些房间在动线上？哪些房间被动线隔开？"
]
```

#### 5. 家具布局/空间利用
```python
questions = [
    "客厅的沙发摆在哪儿？旁边有没有茶几？",
    "餐厅的桌椅是几人座？位置在哪儿？",
    "哪些空间是空余可用未布置的？"
]
```

#### 6. 开间/进深/外墙尺寸
```python
questions = [
    "整栋平面的宽度是多少（包括外墙）？",
    "右侧从窗户到墙的深度约为多少？",
    "最左边的弧形墙体，其弧线半径或宽度大致是多少？"
]
```

#### 7. 视线/可视区域
```python
questions = [
    "从入口处能看到哪些主要空间？",
    "哪些房间是相互可视/无遮挡的？"
]
```

#### 8. 布局异常/冲突点
```python
questions = [
    "有没有墙体穿插、家具重叠或不合理拥挤的地方？",
    "有墙体太薄、门开合冲突等潜在问题吗？"
]
```

#### 9. 转换/输出结构化表达
```python
questions = [
    "请把这个平面图转换成 JSON 格式，包含房间、连通关系、尺寸等属性。",
    "请输出一个结构化表格，每行是一个房间。"
]
```

---

### 二、检索/对比/搜索类

```python
questions = [
    "帮我找图中面积大于 15 平方米的空间有哪些？",
    "查找图中靠窗户的卧室有哪些？",
    "哪些房间与餐厅相连？"
]
```

---

### 三、语义/语境/设计洞察类

#### 1. 设计意图/风格判断
```python
questions = [
    "这张图的布局风格（开放式/分区式）是哪种？",
    "动线设计合理吗？有没有绕行或死角空间？",
    "从布局看这个房子是哪个朝向？采光可能怎么样？"
]
```

#### 2. 建议/优化
```python
questions = [
    "如果这个客厅改成开放式厨房，要怎么改动？",
    "若要增加洗手间，建议放在哪儿？",
    "有没有区域可以扩大或缩减以优化动线？"
]
```

#### 3. 标注解释/符号识别
```python
questions = [
    "图中 '800'、'8120'、'22720' 这些数字是什么意思？",
    "虚线、箭头、红点表示什么符号？",
    "墙体厚度、线宽和注释字体是否有标准意义？"
]
```

---

### 四、模型/系统整合类

#### 1. 结构化辅助
```python
questions = [
    "请输出一个适用于数据库存储的表结构（房间表、连接表、尺寸表等）。",
    "请生成把这张图归档的元数据：房间数、总面积、出口个数等。"
]
```

#### 2. 问答/交互式 QA
```python
questions = [
    "如果用户问：'从入口至次入口要经过哪些房间？' 请给出答案路径。",
    "如果用户问：'哪间卧室最靠近阳台？' 请指出房间名称与位置。"
]
```

#### 3. 错误检测/校验
```python
questions = [
    "请帮我检查这图平面图中有没有尺寸标注错误（不一致/标注重叠）？",
    "有没有家具摆放不合理的地方（阻挡路径/空间不足）？"
]
```

---

## 📊 输出格式

提示词要求 VLM 输出包含以下字段的 JSON：

```json
{
    "answer": "直接回答用户问题的核心内容（简洁明了）",
    "extracted_info": {
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
                "furniture": ["沙发", "茶几"],
                "connected_to": ["餐厅", "卧室1"],
                "windows": 2,
                "doors": 1
            }
        ],
        "annotations": [
            {
                "type": "dimension",
                "value": "22720",
                "parsed_value": 22.72,
                "unit": "m",
                "description": "外墙总长"
            }
        ],
        "symbols": [
            {
                "type": "door",
                "count": 5,
                "positions": ["客厅-餐厅", "卧室1入口"]
            }
        ],
        "circulation": {
            "main_entrance": "底部中央",
            "main_path": "主入口 → 玄关 → 客厅 → 餐厅",
            "layout_type": "开放式客餐厅"
        },
        "design_notes": ["主卧带独立卫生间", "动线流畅"]
    }
}
```

---

## 🧪 测试示例

查看 [example_floor_plan.py](example_floor_plan.py) 获取 **10 个完整示例**：

1. 房间数量识别
2. 尺寸和面积查询
3. 动线分析
4. 家具布局
5. 标注解析
6. 设计评估
7. 条件检索
8. 结构化输出（用于数据库）
9. 交互式问答
10. 批量问题

运行方式：

```bash
cd /home/MuyuWorkSpace/01_TrafficProject/pc_multimodal_rag/backend/image_analysis

# 修改 example_floor_plan.py 中的图片路径
# 取消注释要运行的示例
python example_floor_plan.py
```

---

## ⚙️ 提示词优化要点

### 1. **针对性强**
不同于通用 CAD 图纸，室内平面图提示词：
- 明确图像类型："室内平面布置图"
- 预设常见元素：房间、家具、动线
- 提供具体示例：如 "22720mm = 22.72m"

### 2. **问题导向**
```
**注意事项：**
- 优先回答用户的具体问题，不要罗列所有信息
- 如果用户问"有几个卧室"，就重点回答卧室数量和位置
```

这避免了 VLM 输出冗长无关信息。

### 3. **结构化输出**
提供详细的 JSON Schema，包含：
- `total_dimensions`: 整体尺寸
- `rooms`: 房间数组（包含位置、尺寸、家具、连通关系）
- `annotations`: 标注解析
- `symbols`: 符号识别
- `circulation`: 动线分析
- `design_notes`: 设计建议

### 4. **容错处理**
```
- 如果标注不清晰，标注为"不可读"或给出估算值并说明
```

允许模型在不确定时给出合理估算，而不是拒绝回答。

### 5. **单位换算提示**
```
- 图中尺寸单位通常为毫米(mm)或米(m)，请根据数值大小推断
- 如果涉及尺寸计算，请说明推理过程（如："标注22720mm = 22.72m"）
```

帮助模型正确处理建筑图纸常见的单位问题。

---

## 🔄 与原 CAD 提示词对比

| 维度 | 原 CAD 提示词 | 新 FLOOR_PLAN 提示词 |
|------|--------------|---------------------|
| **适用场景** | 通用工程制造图纸 | 室内平面布置图 |
| **分析重点** | 零件、尺寸、公差、材料 | 房间、动线、家具、空间关系 |
| **输出结构** | 零件信息、视图类型 | 房间数组、动线分析、家具布局 |
| **问题针对性** | 技术参数提取 | 用户具体问题精准回答 |
| **容错性** | 一般 | 强（允许估算和"不可读"） |

---

## 📚 参考场景清单

你提供的所有场景都已覆盖：

- ✅ 结构/布局理解类（9 个子场景）
- ✅ 检索/对比/搜索类（3 个子场景）
- ✅ 语义/语境/设计洞察类（3 个子场景）
- ✅ 模型/系统整合类（3 个子场景）

---

## 🎯 下一步建议

1. **测试覆盖**：使用你的实际 CAD 平面图测试所有场景
2. **迭代优化**：根据测试结果微调提示词
3. **性能优化**：添加缓存、批量处理
4. **集成 OCR**：对于小字标注，结合 PaddleOCR 提高精度

---

## 📞 使用帮助

如有问题，请查看：
- [example_floor_plan.py](example_floor_plan.py) - 完整使用示例
- [simple_vlm_analyzer.py](simple_vlm_analyzer.py#L87-L178) - 提示词源码

或直接运行：
```bash
python example_floor_plan.py
```

---

更新日期：2025-01-XX
优化人员：Claude Agent
