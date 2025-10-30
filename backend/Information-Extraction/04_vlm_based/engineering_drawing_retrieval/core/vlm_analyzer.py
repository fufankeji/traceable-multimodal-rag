"""
VLM图像分析器 - 基于LangChain
"""
import asyncio
import base64
import json
from typing import Dict, List, Optional, Literal
from pathlib import Path
from PIL import Image
import io

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import config, IMAGE_TYPES


class ImageAnalysisResult:
    """图像分析结果"""
    def __init__(
        self,
        image_type: str,
        description: str,
        structured_data: Dict,
        raw_response: str,
        confidence: float = 0.0
    ):
        self.image_type = image_type
        self.description = description
        self.structured_data = structured_data
        self.raw_response = raw_response
        self.confidence = confidence

    def to_dict(self) -> Dict:
        return {
            "image_type": self.image_type,
            "description": self.description,
            "structured_data": self.structured_data,
            "confidence": self.confidence
        }


class EngineeringDrawingAnalyzer:
    """
    工程图纸分析器
    使用LangChain + VLM进行图像语义理解
    """

    def __init__(self):
        self.config = config.vlm

        # 初始化LangChain ChatOpenAI
        self.llm = ChatOpenAI(
            model=self.config.model_name,
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries
        )

        # JSON输出解析器
        self.json_parser = JsonOutputParser()

    def _image_to_base64(self, image_path: str, max_size: int = 2000) -> str:
        """将图像转为base64"""
        img = Image.open(image_path)
        if img.width > max_size or img.height > max_size:
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

        buffer = io.BytesIO()
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        img.save(buffer, format='JPEG', quality=config.image.jpeg_quality)
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode('utf-8')

    def _get_prompt_by_type(self, image_type: str) -> str:
        """根据图像类型获取专用prompt"""
        prompts = {
            "engineering_drawing": """
你是一个专业的工程图纸分析专家。请仔细分析这张工程制造图纸，并提取以下信息：

**分析要求：**
1. **零件信息**：零件名称、编号、材料
2. **尺寸参数**：关键尺寸、公差、配合等级
3. **工艺要求**：表面处理、热处理、加工工艺
4. **技术标注**：所有技术说明、备注、标记
5. **图纸元信息**：图号、版本、日期、设计人

请以JSON格式输出，包含以下字段：
```json
{
    "part_name": "零件名称",
    "part_number": "零件编号",
    "material": "材料",
    "dimensions": ["尺寸1", "尺寸2"],
    "tolerances": ["公差信息"],
    "surface_treatment": "表面处理要求",
    "technical_notes": ["技术标注1", "技术标注2"],
    "drawing_metadata": {
        "drawing_number": "图号",
        "version": "版本",
        "date": "日期"
    },
    "description": "整体描述（100-200字）"
}
```
""",
            "cad_drawing": """
你是一个CAD图纸分析专家。请分析这张CAD技术图纸，提取：

**分析要求：**
1. **结构组成**：主要组件、装配关系
2. **尺寸链**：关键尺寸、配合尺寸
3. **视图信息**：包含的视图类型（主视图、俯视图等）
4. **剖面信息**：剖切位置、剖面线标注
5. **技术参数**：所有可见的参数、规格

JSON输出格式：
```json
{
    "components": ["组件1", "组件2"],
    "assembly_relations": ["装配关系描述"],
    "key_dimensions": ["关键尺寸"],
    "views": ["主视图", "俯视图"],
    "sections": ["剖面A-A"],
    "parameters": {"参数名": "参数值"},
    "description": "CAD图纸整体描述"
}
```
""",
            "floor_plan": """
你是一个专业的建筑/室内平面图分析专家。请分析这张 CAD 平面图（可能是从 CAD 导出的图像格式），并完成以下任务：

**重要说明**：
- 这是一张室内平面布置图，具有大量尺寸标注、家具布置、轴线、文字标签等典型工程制图元素
- 图中尺寸单位需要从标注推断（通常为毫米 mm 或米 m）
- 请仔细识别所有可见的房间、尺寸、符号和标注

**分析要求：**

1. **房间/功能区识别**：
   - 识别所有房间名称（如客厅、卧室、厨房、卫生间、阳台、茶室、书房等）
   - 标注每个房间的位置（如左上、右下、中央等方位描述）
   - 识别特殊功能区（如储藏室、衣帽间、玄关等）

2. **尺寸标注解析**：
   - 提取图中所有可见的尺寸数值（如 800、5790、22720 等）
   - 推断单位（mm/cm/m），并统一换算为米（m）
   - 计算每个房间的长、宽、面积（如果尺寸足够推断）
   - 标注整体平面的外墙尺寸（总长、总宽）

3. **符号与标注识别**：
   - 解释图中符号（虚线=什么、箭头=什么、红点/红线=动线或其他、轴线编号等）
   - 识别所有文字标注（房间编号、面积数值、备注说明等）
   - 说明墙体类型（承重墙/轻质隔墙，如可判断）及厚度
   - 标注门窗位置、类型和开启方向

4. **家具布局识别**：
   - 列出所有可见家具及其所在房间（如沙发、床、餐桌、书桌、茶几等）
   - 标注家具的大致尺寸和位置
   - 判断空间利用率（拥挤/适中/空旷）

5. **动线与空间连通性**：
   - 标出主入口、次入口的位置
   - 描述主要动线路径（如图中红线标注的路径："入口 → 玄关 → 客厅 → ..."）
   - 列出每个房间与哪些房间相连（共用门/开口）
   - 判断布局类型（开放式/分隔式）

6. **设计评估与建议**（可选）：
   - 动线设计是否合理？有无绕行或死角？
   - 采光/朝向如何（如有窗户标注）？
   - 空间优化建议（如可扩大/缩减的区域）

**输出格式要求**：
请严格以 JSON 格式输出，结构如下：
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
        },
        {
            "name": "卧室1",
            "position": "左上",
            "dimensions": {
                "length": 3.6,
                "width": 3.3,
                "area": 11.88,
                "unit": "m"
            },
            "furniture": ["床", "衣柜"],
            "connected_to": ["客厅", "走廊"],
            "windows": 1,
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
        },
        {
            "type": "label",
            "value": "579",
            "description": "可能是房间编号或局部尺寸（5.79m）"
        }
    ],
    "symbols": [
        {
            "type": "door",
            "count": 5,
            "positions": ["客厅-餐厅", "卧室1入口", "卫生间入口"]
        },
        {
            "type": "window",
            "count": 8,
            "positions": ["客厅南侧", "卧室东侧"]
        },
        {
            "type": "circulation_line",
            "description": "红色虚线表示主要动线",
            "path": ["主入口", "玄关", "客厅", "餐厅", "次入口"]
        }
    ],
    "circulation": {
        "main_entrance": "底部中央",
        "secondary_entrance": "右侧",
        "main_path": "主入口 → 玄关 → 客厅 → 餐厅 → 次入口",
        "layout_type": "开放式客餐厅 + 分隔卧室区"
    },
    "design_notes": [
        "主卧带独立卫生间",
        "厨房靠近餐厅，动线合理",
        "客厅与餐厅开放式布局，视野通透",
        "左侧有茶室，功能分区明确"
    ],
    "description": "这是一张约 280㎡ 的室内平面布置图，包含客厅、餐厅、3个卧室、2个卫生间、厨房、茶室等功能区。整体布局采用开放式客餐厅设计，卧室区相对独立，动线流畅，空间利用率高。尺寸标注完整，家具布置合理。"
}
```

**注意事项**：
- 如果尺寸标注模糊或缺失，请标注为 "不可读" 或给出估算值并说明不确定性
- 优先识别主要房间，次要空间可归类为 "其他" 或 "辅助空间"
- 如有多个版本对比，请指出差异部分
- 所有数值计算请提供推断过程（如 "22720mm = 22.72m"）
""",
            "architecture_diagram": """
你是一个系统架构分析专家。请分析这张架构图，提取：

**分析要求：**
1. **系统组件**：所有模块、服务、组件
2. **连接关系**：组件之间的调用、通信关系
3. **技术栈**：使用的技术、框架、协议
4. **层次结构**：分层架构、模块层级
5. **数据流向**：数据流动方向和路径

JSON输出格式：
```json
{
    "components": [
        {"name": "组件名", "type": "服务类型", "technology": "技术栈"}
    ],
    "connections": [
        {"from": "组件A", "to": "组件B", "protocol": "协议", "direction": "方向"}
    ],
    "layers": ["展示层", "业务层", "数据层"],
    "data_flow": ["数据流描述"],
    "description": "架构图整体描述"
}
```
""",
            "flowchart": """
你是一个流程图分析专家。请分析这张流程图，提取：

**分析要求：**
1. **流程节点**：所有步骤、决策点、起止点
2. **流程顺序**：步骤的先后顺序
3. **分支判断**：条件判断、分支路径
4. **角色职责**：涉及的角色、系统
5. **关键路径**：主要流程路径

JSON输出格式：
```json
{
    "nodes": [
        {"id": "节点ID", "type": "类型", "label": "标签", "description": "描述"}
    ],
    "edges": [
        {"from": "节点1", "to": "节点2", "condition": "条件"}
    ],
    "roles": ["角色1", "角色2"],
    "key_paths": ["关键路径描述"],
    "description": "流程图整体描述"
}
```
""",
            "circuit_diagram": """
你是一个电路图分析专家。请分析这张电路图，提取：

**分析要求：**
1. **元器件**：所有电子元件及其参数
2. **连接关系**：元件之间的连接
3. **电路功能**：电路的功能模块
4. **技术参数**：电压、电流、功率等
5. **标注说明**：所有技术标注

JSON输出格式：
```json
{
    "components": [
        {"type": "元件类型", "value": "参数值", "label": "标号"}
    ],
    "connections": ["连接描述"],
    "functional_blocks": ["功能模块"],
    "parameters": {"参数名": "参数值"},
    "description": "电路图整体描述"
}
```
"""
        }

        return prompts.get(image_type, prompts["engineering_drawing"])

    async def analyze_image(
        self,
        image_path: str,
        image_type: str = "engineering_drawing",
        custom_prompt: Optional[str] = None
    ) -> ImageAnalysisResult:
        """
        分析单张图像

        Args:
            image_path: 图像路径
            image_type: 图像类型
            custom_prompt: 自定义prompt（可选）

        Returns:
            ImageAnalysisResult: 分析结果
        """
        # 转换图像为base64
        base64_image = self._image_to_base64(image_path)

        # 获取prompt
        prompt_text = custom_prompt or self._get_prompt_by_type(image_type)

        # 构建消息
        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt_text},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                }
            ]
        )

        # 调用VLM
        try:
            response = await self.llm.ainvoke([message])
            raw_response = response.content

            # 尝试解析JSON
            try:
                # 提取JSON部分（可能包含在markdown代码块中）
                json_str = raw_response
                if "```json" in raw_response:
                    json_str = raw_response.split("```json")[1].split("```")[0].strip()
                elif "```" in raw_response:
                    json_str = raw_response.split("```")[1].split("```")[0].strip()

                structured_data = json.loads(json_str)
                description = structured_data.get("description", "")

            except json.JSONDecodeError:
                # 如果无法解析JSON，使用原始文本
                structured_data = {"raw_text": raw_response}
                description = raw_response[:500]  # 取前500字符

            return ImageAnalysisResult(
                image_type=image_type,
                description=description,
                structured_data=structured_data,
                raw_response=raw_response,
                confidence=0.85  # 可以后续添加置信度评估
            )

        except Exception as e:
            print(f"VLM分析失败: {e}")
            raise

    async def analyze_batch(
        self,
        image_paths: List[str],
        image_type: str = "engineering_drawing",
        max_concurrent: Optional[int] = None
    ) -> List[ImageAnalysisResult]:
        """
        批量分析图像（异步并发）

        Args:
            image_paths: 图像路径列表
            image_type: 图像类型
            max_concurrent: 最大并发数

        Returns:
            List[ImageAnalysisResult]: 分析结果列表
        """
        max_concurrent = max_concurrent or self.config.max_concurrent

        # 创建信号量控制并发
        semaphore = asyncio.Semaphore(max_concurrent)

        async def analyze_with_semaphore(path):
            async with semaphore:
                try:
                    return await self.analyze_image(path, image_type)
                except Exception as e:
                    print(f"分析失败 {path}: {e}")
                    return None

        # 并发执行
        tasks = [analyze_with_semaphore(path) for path in image_paths]
        results = await asyncio.gather(*tasks)

        # 过滤None结果
        return [r for r in results if r is not None]

    async def classify_image_type(self, image_path: str) -> str:
        """
        自动识别图像类型

        Args:
            image_path: 图像路径

        Returns:
            str: 图像类型
        """
        base64_image = self._image_to_base64(image_path)

        classification_prompt = f"""
请判断这张图片属于以下哪种类型：

{chr(10).join(f"{k}: {v}" for k, v in IMAGE_TYPES.items())}

只需要返回类型的英文标识符（如 engineering_drawing），不需要其他解释。
"""

        message = HumanMessage(
            content=[
                {"type": "text", "text": classification_prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                }
            ]
        )

        try:
            response = await self.llm.ainvoke([message])
            predicted_type = response.content.strip().lower()

            # 验证返回的类型
            if predicted_type in IMAGE_TYPES:
                return predicted_type
            else:
                # 默认返回工程图纸
                return "engineering_drawing"

        except Exception as e:
            print(f"图像分类失败: {e}")
            return "engineering_drawing"


# 便捷函数
async def analyze_engineering_drawing(image_path: str) -> ImageAnalysisResult:
    """快速分析工程图纸"""
    analyzer = EngineeringDrawingAnalyzer()
    return await analyzer.analyze_image(image_path, "engineering_drawing")


async def analyze_with_auto_type(image_path: str) -> ImageAnalysisResult:
    """自动识别类型并分析"""
    analyzer = EngineeringDrawingAnalyzer()
    image_type = await analyzer.classify_image_type(image_path)
    print(f"识别的图像类型: {IMAGE_TYPES[image_type]}")
    return await analyzer.analyze_image(image_path, image_type)


if __name__ == "__main__":
    # 测试代码
    async def test():
        analyzer = EngineeringDrawingAnalyzer()

        # 测试单张图片
        test_image = "/path/to/engineering_drawing.png"
        if Path(test_image).exists():
            result = await analyzer.analyze_image(test_image)
            print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))

    asyncio.run(test())
